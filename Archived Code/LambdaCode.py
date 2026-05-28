import json, boto3, uuid, datetime

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('JusticeArchDocuments')

def lambda_handler(event, context):
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key = record['s3']['object']['key']

    # Call Textract to extract key-value pairs
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']
    )

    blocks = response.get('Blocks', [])
    vendor = ''
    date = ''
    amount = ''
    scores = []

    for block in blocks:
        if block['BlockType'] == 'KEY_VALUE_SET':
            conf = block.get('Confidence', 0)
            scores.append(conf)
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'VALUE':
                        for value_id in relationship['Ids']:
                            for value_block in blocks:
                                if value_block['Id'] == value_id and value_block['BlockType'] == 'WORD':
                                    text = value_block.get('Text', '').lower()
                                    if 'vendor' in block.get('Text', '').lower():
                                        vendor = text
                                    if 'date' in block.get('Text', '').lower():
                                        date = text
                                    if 'amount' in block.get('Text', '').lower() or 'total' in block.get('Text', '').lower():
                                        amount = text

    avg_confidence = sum(scores) / len(scores) if scores else 0
    flagged = avg_confidence < 80.0

    doc_id = str(uuid.uuid4())
    table.put_item(Item={
        'documentId': doc_id,
        's3Key': key,
        'vendor': vendor or 'UNKNOWN',
        'date': date or 'UNKNOWN',
        'amount': amount or 'UNKNOWN',
        'confidence': str(round(avg_confidence, 2)),
        'flaggedForReview': flagged,
        'status': 'PENDING',
        'uploadedAt': datetime.datetime.utcnow().isoformat()
    })

    print(f'Processed {key}: confidence={avg_confidence:.1f}%, flagged={flagged}')
    return {'statusCode': 200, 'body': json.dumps('Done')}