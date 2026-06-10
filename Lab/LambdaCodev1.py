import json, boto3, uuid, datetime, re

s3       = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
sns      = boto3.client('sns', region_name='ap-southeast-1')
table    = dynamodb.Table('JusticeArchDocuments')

SNS_TOPIC_ARN = 'arn:aws:sns:ap-southeast-1:393323650223:JusticeArch-ReviewAlert'

def get_text(block, blocks_map):
    """Follow relationships to extract actual text from a block."""
    text = ''
    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for child_id in rel['Ids']:
                child = blocks_map.get(child_id, {})
                if child.get('BlockType') == 'WORD':
                    text += child.get('Text', '') + ' '
    return text.strip()

def lambda_handler(event, context):
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key    = record['s3']['object']['key']

    # ── Step 1: Call Textract (both FORMS and raw text) ──────────────────
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']
    )

    blocks     = response.get('Blocks', [])
    blocks_map = {b['Id']: b for b in blocks}

    # ── Step 2: Build key-value pairs from FORMS ──────────────────────────
    kv_pairs = {}
    scores   = []

    for block in blocks:
        if block['BlockType'] == 'KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            conf = block.get('Confidence', 0)
            scores.append(conf)

            key_text = get_text(block, blocks_map)

            # Find the VALUE block linked to this KEY
            val_text = ''
            for rel in block.get('Relationships', []):
                if rel['Type'] == 'VALUE':
                    for val_id in rel['Ids']:
                        val_block = blocks_map.get(val_id, {})
                        val_text  = get_text(val_block, blocks_map)

            if key_text:
                kv_pairs[key_text.lower().strip(':')] = val_text

    # ── Step 3: Also collect all LINE text for fallback regex search ──────
    all_lines = []
    for block in blocks:
        if block['BlockType'] == 'LINE':
            all_lines.append(block.get('Text', ''))

    full_text = '\n'.join(all_lines)

    # ── Step 4: Extract Vendor ────────────────────────────────────────────
    vendor = 'UNKNOWN'

    # Try key-value pairs first
    for k, v in kv_pairs.items():
        if any(word in k for word in ['vendor', 'from', 'supplier', 'company', 'billed by']):
            if v:
                vendor = v
                break

    # Fallback: look for lines after FROM keyword
    if vendor == 'UNKNOWN':
        lines_lower = [l.lower() for l in all_lines]
        for i, line in enumerate(lines_lower):
            if line.strip() in ['from', 'vendor:', 'supplier:']:
                if i + 1 < len(all_lines):
                    vendor = all_lines[i + 1]
                    break

    # Fallback: grab line after "FROM" if it appears inline
    if vendor == 'UNKNOWN':
        match = re.search(r'FROM\s*\n(.+)', full_text)
        if match:
            vendor = match.group(1).strip()

    # ── Step 5: Extract Date ──────────────────────────────────────────────
    date = 'UNKNOWN'

    # Try key-value pairs
    for k, v in kv_pairs.items():
        if any(word in k for word in ['date', 'invoice date', 'issued']):
            if v:
                date = v
                break

    # Fallback: regex for date patterns in full text
    if date == 'UNKNOWN':
        patterns = [
            r'\b(\d{1,2}[\s\/\-]\w+[\s\/\-]\d{4})\b',   # 15 January 2024
            r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b',  # 15/01/2024
            r'\b(\w+ \d{1,2},?\s*\d{4})\b',               # January 15, 2024
        ]
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                date = match.group(1)
                break

    # ── Step 6: Extract Amount ────────────────────────────────────────────
    amount = 'UNKNOWN'

    # Try key-value pairs
    for k, v in kv_pairs.items():
        if any(word in k for word in ['total', 'amount due', 'amount', 'grand total', 'balance']):
            if v:
                amount = v
                break

    # Fallback: regex for currency amounts
    if amount == 'UNKNOWN':
        # Look for total amount line
        match = re.search(
            r'(?:total amount due|grand total|amount due|total)[^\d]*'
            r'((?:RM|USD|\$|MYR)[\s]*[\d,]+\.?\d*)',
            full_text, re.IGNORECASE
        )
        if match:
            amount = match.group(1).strip()

    # Last resort: find the largest currency amount in the document
    if amount == 'UNKNOWN':
        currency_amounts = re.findall(
            r'((?:RM|USD|\$|MYR)\s*[\d,]+\.?\d{0,2})', full_text, re.IGNORECASE
        )
        if currency_amounts:
            amount = currency_amounts[-1]  # Usually the total is last

    # ── Step 7: Calculate confidence & save to DynamoDB ──────────────────
    avg_confidence = sum(scores) / len(scores) if scores else 50.0

    # Three-tier confidence logic:
    # >= 80%  → auto-approved
    # 60-79%  → pending review (normal priority)
    # < 60%   → pending review (high priority, highlighted)
    if avg_confidence >= 80.0:
        status           = 'APPROVED'
        flagged          = False
        review_priority  = 'NORMAL'
    elif avg_confidence >= 60.0:
        status           = 'PENDING'
        flagged          = True
        review_priority  = 'NORMAL'
    else:
        status           = 'PENDING'
        flagged          = True
        review_priority  = 'HIGH'

    doc_id = str(uuid.uuid4())
    table.put_item(Item={
        'documentId':      doc_id,
        's3Key':           key,
        'vendor':          vendor,
        'date':            date,
        'amount':          amount,
        'confidence':      str(round(avg_confidence, 2)),
        'flaggedForReview': flagged,
        'reviewPriority':  review_priority,
        'status':          status,
        'uploadedAt':      datetime.datetime.utcnow().isoformat(),
        'rawKVPairs':      json.dumps(kv_pairs)
    })

    # ── Step 8: Send SNS notification if human review is needed ──────────
    if flagged:
        if review_priority == 'HIGH':
            subject = '🔴 [URGENT] JusticeArch – Low Confidence Document Requires Review'
            message = (
                f"URGENT REVIEW REQUIRED\n"
                f"{'='*50}\n\n"
                f"A document was processed with VERY LOW confidence and requires immediate attention.\n\n"
                f"Document Details:\n"
                f"  File     : {key}\n"
                f"  Doc ID   : {doc_id}\n"
                f"  Vendor   : {vendor}\n"
                f"  Date     : {date}\n"
                f"  Amount   : {amount}\n"
                f"  Confidence: {avg_confidence:.1f}% (below 60% threshold)\n"
                f"  Priority : HIGH — please review immediately\n\n"
                f"Action Required:\n"
                f"  Log in to the JusticeArch Review Portal and verify this document.\n"
            )
        else:
            subject = '⚠️ [ACTION NEEDED] JusticeArch – Document Pending Review'
            message = (
                f"DOCUMENT PENDING REVIEW\n"
                f"{'='*50}\n\n"
                f"A document was processed with moderate confidence and requires human review.\n\n"
                f"Document Details:\n"
                f"  File     : {key}\n"
                f"  Doc ID   : {doc_id}\n"
                f"  Vendor   : {vendor}\n"
                f"  Date     : {date}\n"
                f"  Amount   : {amount}\n"
                f"  Confidence: {avg_confidence:.1f}% (between 60–79%)\n"
                f"  Priority : NORMAL\n\n"
                f"Action Required:\n"
                f"  Log in to the JusticeArch Review Portal to approve or reject this document.\n"
            )

        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=message
            )
            print(f"SNS notification sent | Priority={review_priority}")
        except Exception as e:
            print(f"SNS notification failed: {e}")

    print(f"Processed: {key}")
    print(f"Vendor={vendor} | Date={date} | Amount={amount}")
    print(f"Confidence={avg_confidence:.1f}% | Flagged={flagged} | Status={status} | Priority={review_priority}")
    print(f"KV Pairs found: {list(kv_pairs.keys())}")

    return {'statusCode': 200, 'body': json.dumps('Done')}
    