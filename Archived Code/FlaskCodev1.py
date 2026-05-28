from flask import Flask, render_template_string, request, redirect, url_for
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
table = dynamodb.Table('JusticeArchDocuments')

BUCKET_NAME = 'justicearch-inbox-group7'   # ← replace with your actual bucket name

def get_presigned_url(s3_key):
    """Generate a temporary URL so admin can open the PDF in browser."""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300   # URL valid for 5 minutes
        )
        return url
    except ClientError:
        return None

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
  <title>JusticeArch Review Portal</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; background: #f0f4f8; color: #222; }

    /* ── Top bar ── */
    .topbar {
      background: #1F4E79; color: white;
      padding: 16px 32px; display: flex;
      align-items: center; justify-content: space-between;
    }
    .topbar h1 { font-size: 20px; }
    .topbar span { font-size: 13px; opacity: 0.75; }

    /* ── Stats row ── */
    .stats {
      display: flex; gap: 16px;
      padding: 20px 32px; background: #e8f0f7;
      border-bottom: 1px solid #ccd9e8;
    }
    .stat-box {
      background: white; border-radius: 8px;
      padding: 14px 24px; text-align: center;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08); min-width: 130px;
    }
    .stat-box .num { font-size: 28px; font-weight: bold; }
    .stat-box .lbl { font-size: 12px; color: #666; margin-top: 4px; }
    .num.green  { color: #1a7f4b; }
    .num.red    { color: #c0392b; }
    .num.orange { color: #e67e22; }
    .num.blue   { color: #1F4E79; }

    /* ── Main content ── */
    .content { padding: 24px 32px; }

    /* ── Search bar ── */
    .searchbar { display: flex; gap: 10px; margin-bottom: 20px; }
    .searchbar input {
      flex: 1; padding: 10px 14px; border: 1px solid #b0c4d8;
      border-radius: 6px; font-size: 14px;
    }
    .searchbar button {
      padding: 10px 22px; background: #1F4E79; color: white;
      border: none; border-radius: 6px; cursor: pointer; font-size: 14px;
    }
    .searchbar a {
      padding: 10px 18px; background: #6c757d; color: white;
      border-radius: 6px; text-decoration: none; font-size: 14px;
    }

    /* ── Table ── */
    .table-wrap { overflow-x: auto; background: white;
                  border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    table { width: 100%; border-collapse: collapse; min-width: 900px; }
    th {
      background: #1F4E79; color: white;
      padding: 12px 10px; text-align: left; font-size: 13px;
    }
    td { padding: 10px; border-bottom: 1px solid #e0eaf4; font-size: 13px; vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f5f9ff; }

    /* ── Badges ── */
    .badge {
      display: inline-block; padding: 3px 10px; border-radius: 12px;
      font-size: 11px; font-weight: bold; text-transform: uppercase;
    }
    .badge-approved { background: #d4edda; color: #1a7f4b; }
    .badge-pending  { background: #fff3cd; color: #856404; }
    .badge-rejected { background: #f8d7da; color: #842029; }

    .conf-high { color: #1a7f4b; font-weight: bold; }
    .conf-low  { color: #c0392b; font-weight: bold; }

    /* ── Action buttons ── */
    .btn {
      padding: 6px 12px; border: none; border-radius: 5px;
      cursor: pointer; font-size: 12px; font-weight: bold;
      text-decoration: none; display: inline-block; margin: 2px;
    }
    .btn-view     { background: #0d6efd; color: white; }
    .btn-approve  { background: #198754; color: white; }
    .btn-reject   { background: #dc3545; color: white; }
    .btn-disabled { background: #ccc; color: #888; cursor: not-allowed; }

    /* ── Modal overlay ── */
    .modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.65); z-index: 1000;
      align-items: center; justify-content: center;
    }
    .modal-overlay.active { display: flex; }
    .modal {
      background: white; border-radius: 12px; width: 90vw; max-width: 980px;
      max-height: 92vh; display: flex; flex-direction: column;
      box-shadow: 0 8px 40px rgba(0,0,0,0.35); overflow: hidden;
    }
    .modal-header {
      background: #1F4E79; color: white;
      padding: 14px 20px; display: flex;
      justify-content: space-between; align-items: center;
    }
    .modal-header h3 { font-size: 16px; }
    .modal-close {
      background: none; border: none; color: white;
      font-size: 22px; cursor: pointer; line-height: 1;
    }
    .modal-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
    .modal-body iframe { flex: 1; width: 100%; border: none; min-height: 500px; }

    /* ── PDF info panel inside modal ── */
    .pdf-meta {
      padding: 12px 18px; background: #f8f9fa;
      border-bottom: 1px solid #dee2e6;
      display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px;
    }
    .pdf-meta span b { color: #1F4E79; }

    /* ── Reject form inside modal ── */
    .reject-section {
      padding: 14px 18px; background: #fff8f8;
      border-top: 2px solid #f8d7da;
    }
    .reject-section h4 { color: #842029; margin-bottom: 10px; font-size: 14px; }
    .reject-section textarea {
      width: 100%; padding: 8px; border: 1px solid #f5c2c7;
      border-radius: 6px; font-size: 13px; resize: vertical; min-height: 70px;
    }
    .reject-actions { display: flex; gap: 10px; margin-top: 10px; }

    /* ── Approve section inside modal ── */
    .approve-section {
      padding: 14px 18px; background: #f0fff4;
      border-top: 2px solid #d4edda; display: flex;
      align-items: center; justify-content: space-between;
    }
    .approve-section p { font-size: 13px; color: #1a7f4b; }

    /* ── Alert banner ── */
    .alert {
      padding: 12px 18px; border-radius: 8px; margin-bottom: 18px; font-size: 14px;
    }
    .alert-info { background: #cfe2ff; border: 1px solid #9ec5fe; color: #084298; }
  </style>
</head>
<body>

<!-- Top bar -->
<div class="topbar">
  <h1>☁ JusticeArch Document Review Portal</h1>
  <span>Powered by AWS Textract + DynamoDB</span>
</div>

<!-- Stats -->
<div class="stats">
  <div class="stat-box">
    <div class="num blue">{{ total }}</div>
    <div class="lbl">Total Documents</div>
  </div>
  <div class="stat-box">
    <div class="num green">{{ approved }}</div>
    <div class="lbl">Auto-Approved</div>
  </div>
  <div class="stat-box">
    <div class="num orange">{{ pending }}</div>
    <div class="lbl">Pending Review</div>
  </div>
  <div class="stat-box">
    <div class="num red">{{ rejected }}</div>
    <div class="lbl">Rejected</div>
  </div>
</div>

<!-- Main content -->
<div class="content">

  <!-- Search -->
  <form class="searchbar" method="GET" action="/search">
    <input name="q" placeholder="Search by vendor, date, amount, status..."
           value="{{ query or '' }}">
    <button type="submit">🔍 Search</button>
    <a href="/">Clear</a>
  </form>

  {% if query %}
  <div class="alert alert-info">
    Showing results for: <b>"{{ query }}"</b> — {{ docs|length }} record(s) found.
  </div>
  {% endif %}

  <!-- Table -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Doc ID</th>
          <th>File Name</th>
          <th>Vendor</th>
          <th>Date</th>
          <th>Amount</th>
          <th>Confidence</th>
          <th>Status</th>
          <th>Uploaded</th>
          <th style="text-align:center">Actions</th>
        </tr>
      </thead>
      <tbody>
      {% for doc in docs %}
        <tr>
          <td><code style="font-size:11px">{{ doc.documentId[:8] }}...</code></td>
          <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="{{ doc.s3Key }}">{{ doc.s3Key }}</td>
          <td>{{ doc.vendor }}</td>
          <td>{{ doc.date }}</td>
          <td><b>{{ doc.amount }}</b></td>
          <td>
            {% set conf = doc.confidence | float %}
            <span class="{{ 'conf-low' if conf < 80 else 'conf-high' }}">
              {{ doc.confidence }}%
              {% if conf < 80 %}⚠️{% else %}✅{% endif %}
            </span>
          </td>
          <td>
            {% if doc.status == 'APPROVED' %}
              <span class="badge badge-approved">✓ Approved</span>
            {% elif doc.status == 'REJECTED' %}
              <span class="badge badge-rejected">✗ Rejected</span>
              {% if doc.rejectReason %}
                <div style="font-size:11px;color:#842029;margin-top:4px">
                  Reason: {{ doc.rejectReason }}
                </div>
              {% endif %}
            {% else %}
              <span class="badge badge-pending">⏳ Pending</span>
            {% endif %}
          </td>
          <td style="font-size:11px;color:#666">
            {{ doc.uploadedAt[:10] if doc.uploadedAt else '-' }}
          </td>
          <td style="text-align:center;white-space:nowrap">
            {% if doc.flaggedForReview and doc.status == 'PENDING' %}
              <!-- Low confidence: show View + Approve + Reject -->
              <button class="btn btn-view"
                onclick="openModal(
                  '{{ doc.documentId }}',
                  '{{ doc.s3Key }}',
                  '{{ doc.vendor }}',
                  '{{ doc.date }}',
                  '{{ doc.amount }}',
                  '{{ doc.confidence }}',
                  '{{ doc.pdfUrl }}'
                )">📄 View PDF</button>
            {% elif doc.status == 'PENDING' %}
              <!-- High conf but still pending -->
              <form method="POST" action="/approve" style="display:inline">
                <input type="hidden" name="id" value="{{ doc.documentId }}">
                <button class="btn btn-approve">✓ Approve</button>
              </form>
            {% else %}
              <span class="btn btn-disabled">{{ doc.status }}</span>
            {% endif %}
          </td>
        </tr>
      {% endfor %}
      {% if not docs %}
        <tr>
          <td colspan="9" style="text-align:center;padding:30px;color:#888">
            No documents found.
          </td>
        </tr>
      {% endif %}
      </tbody>
    </table>
  </div>
</div>

<!-- ── PDF Review Modal ─────────────────────────────────────────────────── -->
<div class="modal-overlay" id="pdfModal">
  <div class="modal">

    <div class="modal-header">
      <h3>📄 PDF Review — <span id="modalTitle"></span></h3>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>

    <div class="modal-body">

      <!-- Metadata strip -->
      <div class="pdf-meta">
        <span><b>Vendor:</b> <span id="mVendor"></span></span>
        <span><b>Date:</b> <span id="mDate"></span></span>
        <span><b>Amount:</b> <span id="mAmount"></span></span>
        <span><b>Confidence:</b> <span id="mConf" style="color:#c0392b;font-weight:bold"></span>%</span>
        <span style="color:#856404">⚠️ Low confidence — please verify the PDF before approving.</span>
      </div>

      <!-- PDF viewer -->
      <iframe id="pdfFrame" src="" title="Invoice PDF"></iframe>

      <!-- Approve section -->
      <div class="approve-section">
        <p>✅ Document looks correct? Approve it below.</p>
        <form method="POST" action="/approve" id="approveForm">
          <input type="hidden" name="id" id="approveId">
          <button class="btn btn-approve" style="padding:10px 24px;font-size:14px">
            ✓ Approve Document
          </button>
        </form>
      </div>

      <!-- Reject section -->
      <div class="reject-section">
        <h4>✗ Reject this document</h4>
        <form method="POST" action="/reject" id="rejectForm">
          <input type="hidden" name="id" id="rejectId">
          <textarea name="reason"
            placeholder="Enter reason for rejection (e.g. Wrong vendor name, Amount mismatch, Duplicate invoice, Unreadable document...)"></textarea>
          <div class="reject-actions">
            <button class="btn btn-reject" type="submit"
                    style="padding:8px 20px;font-size:13px">
              ✗ Reject Document
            </button>
            <span style="font-size:12px;color:#888;align-self:center">
              A reason is recommended before rejecting.
            </span>
          </div>
        </form>
      </div>

    </div>
  </div>
</div>

<script>
function openModal(docId, s3Key, vendor, date, amount, conf, pdfUrl) {
  document.getElementById('modalTitle').textContent = s3Key;
  document.getElementById('mVendor').textContent    = vendor;
  document.getElementById('mDate').textContent      = date;
  document.getElementById('mAmount').textContent    = amount;
  document.getElementById('mConf').textContent      = conf;
  document.getElementById('approveId').value        = docId;
  document.getElementById('rejectId').value         = docId;

  // Load PDF in iframe if URL exists
  if (pdfUrl && pdfUrl !== 'None') {
    document.getElementById('pdfFrame').src = pdfUrl;
  } else {
    document.getElementById('pdfFrame').src =
      'data:text/html,<p style="font-family:Arial;padding:40px;color:#888">' +
      'PDF preview unavailable. Check S3 bucket permissions.</p>';
  }

  document.getElementById('pdfModal').classList.add('active');
}

function closeModal() {
  document.getElementById('pdfModal').classList.remove('active');
  document.getElementById('pdfFrame').src = '';
}

// Close modal when clicking outside
document.getElementById('pdfModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});
</script>

</body>
</html>
'''

def get_all_docs():
    result = table.scan()
    items  = result.get('Items', [])
    # Generate presigned URL for flagged docs
    for doc in items:
        if doc.get('flaggedForReview') and doc.get('status') == 'PENDING':
            doc['pdfUrl'] = get_presigned_url(doc.get('s3Key', ''))
        else:
            doc['pdfUrl'] = None
    return items

def calc_stats(docs):
    return {
        'total':    len(docs),
        'approved': sum(1 for d in docs if d.get('status') == 'APPROVED'),
        'pending':  sum(1 for d in docs if d.get('status') == 'PENDING'),
        'rejected': sum(1 for d in docs if d.get('status') == 'REJECTED'),
    }

@app.route('/')
def index():
    docs  = get_all_docs()
    stats = calc_stats(docs)
    return render_template_string(TEMPLATE, docs=docs, query=None, **stats)

@app.route('/search')
def search():
    q     = request.args.get('q', '').strip()
    docs  = get_all_docs()
    if q:
        docs = [d for d in docs if q.lower() in str(d).lower()]
    stats = calc_stats(docs)
    return render_template_string(TEMPLATE, docs=docs, query=q, **stats)

@app.route('/approve', methods=['POST'])
def approve():
    doc_id = request.form['id']
    table.update_item(
        Key={'documentId': doc_id},
        UpdateExpression='SET #s = :v, flaggedForReview = :f',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':v': 'APPROVED', ':f': False}
    )
    return redirect('/')

@app.route('/reject', methods=['POST'])
def reject():
    doc_id = request.form['id']
    reason = request.form.get('reason', 'No reason provided').strip()
    table.update_item(
        Key={'documentId': doc_id},
        UpdateExpression='SET #s = :v, rejectReason = :r, flaggedForReview = :f',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':v': 'REJECTED',
            ':r': reason,
            ':f': False
        }
    )
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)