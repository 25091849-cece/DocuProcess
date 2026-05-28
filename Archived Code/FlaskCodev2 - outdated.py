from flask import Flask, render_template_string, request, redirect, url_for, flash, jsonify
import boto3, os
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'justicearch-secret-2024'

dynamodb  = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
table     = dynamodb.Table('JusticeArchDocuments')

BUCKET_NAME  = 'justicearch-inbox-group7'   # ← replace with your actual bucket name
MAX_UPLOADS  = 3

def get_presigned_url(s3_key):
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=300
        )
    except ClientError:
        return None

def get_all_docs():
    result = table.scan()
    items  = result.get('Items', [])
    for doc in items:
        if doc.get('flaggedForReview') and doc.get('status') == 'PENDING':
            doc['pdfUrl'] = get_presigned_url(doc.get('s3Key', '')) or ''
        else:
            doc['pdfUrl'] = ''
    return items

def calc_stats(docs):
    return {
        'total':    len(docs),
        'approved': sum(1 for d in docs if d.get('status') == 'APPROVED'),
        'pending':  sum(1 for d in docs if d.get('status') == 'PENDING'),
        'rejected': sum(1 for d in docs if d.get('status') == 'REJECTED'),
    }

# ── Shared CSS & layout ────────────────────────────────────────────────────────
BASE_STYLE = '''
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, sans-serif; background: #f0f4f8; color: #222; }

  .topbar {
    background: #1F4E79; color: white;
    padding: 16px 32px; display: flex;
    align-items: center; justify-content: space-between;
  }
  .topbar h1 { font-size: 20px; }
  .topbar span { font-size: 13px; opacity: 0.75; }

  /* ── Tabs ── */
  .tab-bar {
    background: #163d61; display: flex; gap: 0;
    padding: 0 32px; border-bottom: 3px solid #0d2b47;
  }
  .tab-bar a {
    display: inline-block; padding: 13px 28px;
    color: rgba(255,255,255,0.65); text-decoration: none;
    font-size: 14px; font-weight: bold; border-bottom: 3px solid transparent;
    margin-bottom: -3px; transition: all 0.2s;
  }
  .tab-bar a:hover { color: white; background: rgba(255,255,255,0.07); }
  .tab-bar a.active { color: white; border-bottom: 3px solid #5bc0eb; }

  .stats {
    display: flex; gap: 16px; padding: 20px 32px;
    background: #e8f0f7; border-bottom: 1px solid #ccd9e8; flex-wrap: wrap;
  }
  .stat-box {
    background: white; border-radius: 8px; padding: 14px 24px;
    text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,0.08); min-width: 130px;
  }
  .stat-box .num { font-size: 28px; font-weight: bold; }
  .stat-box .lbl { font-size: 12px; color: #666; margin-top: 4px; }
  .num.green  { color: #1a7f4b; }
  .num.red    { color: #c0392b; }
  .num.orange { color: #e67e22; }
  .num.blue   { color: #1F4E79; }

  .content { padding: 24px 32px; }

  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 12px;
    font-size: 11px; font-weight: bold; text-transform: uppercase;
  }
  .badge-approved { background: #d4edda; color: #1a7f4b; }
  .badge-pending  { background: #fff3cd; color: #856404; }
  .badge-rejected { background: #f8d7da; color: #842029; }

  .btn {
    padding: 5px 10px; border: none; border-radius: 5px;
    cursor: pointer; font-size: 11px; font-weight: bold;
    display: inline-block; margin: 2px; white-space: nowrap;
  }
  .btn-view    { background: #0d6efd; color: white; }
  .btn-approve { background: #198754; color: white; }
  .btn-reject  { background: #dc3545; color: white; }
  .btn-disabled{ background: #e0e0e0; color: #999; cursor: not-allowed; }

  .conf-high { color: #1a7f4b; font-weight: bold; }
  .conf-low  { color: #c0392b; font-weight: bold; }

  /* ── Search ── */
  .searchbar { display: flex; gap: 10px; margin-bottom: 8px; }
  .search-wrap { position: relative; flex: 1; }
  .search-wrap input {
    width: 100%; padding: 10px 40px 10px 14px;
    border: 2px solid #b0c4d8; border-radius: 6px;
    font-size: 14px; outline: none; transition: border-color 0.2s;
  }
  .search-wrap input:focus { border-color: #1F4E79; }
  .search-wrap .clear-btn {
    position: absolute; right: 10px; top: 50%;
    transform: translateY(-50%); background: none;
    border: none; font-size: 18px; color: #999;
    cursor: pointer; display: none;
  }
  .search-wrap .clear-btn.visible { display: block; }
  .search-spinner {
    position: absolute; right: 36px; top: 50%;
    transform: translateY(-50%); display: none;
    width: 16px; height: 16px; border: 2px solid #ccc;
    border-top-color: #1F4E79; border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  .search-spinner.visible { display: block; }
  @keyframes spin { to { transform: translateY(-50%) rotate(360deg); } }
  .search-hint { font-size: 12px; color: #888; margin-bottom: 16px; }
  .search-hint b { color: #1F4E79; }
  .result-count {
    font-size: 13px; color: #555; margin-bottom: 12px;
    padding: 8px 14px; background: #dbeafe; border-radius: 6px;
    border-left: 4px solid #1F4E79; display: none;
  }
  .result-count.visible { display: block; }

  /* ── Table ── */
  .table-wrap {
    overflow-x: auto; background: white;
    border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  table { width: 100%; border-collapse: collapse; min-width: 960px; }
  th {
    background: #1F4E79; color: white;
    padding: 12px 10px; text-align: left; font-size: 13px;
  }
  td {
    padding: 10px; border-bottom: 1px solid #e0eaf4;
    font-size: 13px; vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #f5f9ff; }
  .highlight-text { background: #fff176; border-radius: 3px; padding: 1px 2px; }

  /* ── Inline reject ── */
  .reject-inline {
    display: none; margin-top: 8px; padding: 10px;
    background: #fff5f5; border: 1px solid #f5c2c7; border-radius: 6px;
  }
  .reject-inline.open { display: block; }
  .reject-inline textarea {
    width: 100%; padding: 7px; font-size: 12px;
    border: 1px solid #f5c2c7; border-radius: 4px;
    resize: vertical; min-height: 60px; margin-bottom: 7px;
  }
  .reject-inline .hint { font-size: 11px; color: #888; margin-bottom: 6px; display: block; }
  .reject-inline .actions { display: flex; gap: 6px; }

  /* ── Modal ── */
  .modal-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.65); z-index: 1000;
    align-items: center; justify-content: center;
  }
  .modal-overlay.active { display: flex; }
  .modal {
    background: white; border-radius: 12px;
    width: 92vw; max-width: 1000px; max-height: 93vh;
    display: flex; flex-direction: column;
    box-shadow: 0 8px 40px rgba(0,0,0,0.35); overflow: hidden;
  }
  .modal-header {
    background: #1F4E79; color: white; padding: 14px 20px;
    display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;
  }
  .modal-header h3 { font-size: 15px; }
  .modal-close { background: none; border: none; color: white; font-size: 22px; cursor: pointer; }
  .pdf-meta {
    padding: 10px 18px; background: #f8f9fa; border-bottom: 1px solid #dee2e6;
    display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; flex-shrink: 0;
  }
  .pdf-meta span b { color: #1F4E79; }
  .modal-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; }
  .modal-body iframe { flex: 1; width: 100%; border: none; min-height: 420px; }
  .modal-approve {
    padding: 12px 18px; background: #f0fff4; border-top: 2px solid #d4edda;
    display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
  }
  .modal-approve p { font-size: 13px; color: #1a7f4b; }
  .modal-reject { padding: 12px 18px; background: #fff8f8; border-top: 2px solid #f8d7da; flex-shrink: 0; }
  .modal-reject h4 { color: #842029; margin-bottom: 8px; font-size: 13px; }
  .modal-reject textarea {
    width: 100%; padding: 8px; border: 1px solid #f5c2c7;
    border-radius: 5px; font-size: 13px; resize: vertical; min-height: 65px;
  }
  .modal-reject .actions { display: flex; gap: 8px; margin-top: 8px; align-items: center; }
  .modal-reject .hint-txt { font-size: 11px; color: #999; }
</style>
'''

TOPBAR = '''
<div class="topbar">
  <h1>☁ JusticeArch Document Review Portal</h1>
  <span>AWS Textract + DynamoDB Pipeline</span>
</div>
<div class="tab-bar">
  <a href="/" class="{{ 'active' if active_tab == 'review' else '' }}">📋 Review Portal</a>
  <a href="/upload" class="{{ 'active' if active_tab == 'upload' else '' }}">📤 Upload PDF</a>
</div>
'''

# ── REVIEW PAGE TEMPLATE ───────────────────────────────────────────────────────
REVIEW_TEMPLATE = BASE_STYLE + '''
<div class="topbar">
  <h1>☁ JusticeArch Document Review Portal</h1>
  <span>AWS Textract + DynamoDB Pipeline</span>
</div>
<div class="tab-bar">
  <a href="/" class="active">📋 Review Portal</a>
  <a href="/upload">📤 Upload PDF</a>
</div>

<div class="stats">
  <div class="stat-box"><div class="num blue">{{ total }}</div><div class="lbl">Total Documents</div></div>
  <div class="stat-box"><div class="num green">{{ approved }}</div><div class="lbl">Auto-Approved</div></div>
  <div class="stat-box"><div class="num orange">{{ pending }}</div><div class="lbl">Pending Review</div></div>
  <div class="stat-box"><div class="num red">{{ rejected }}</div><div class="lbl">Rejected</div></div>
</div>

<div class="content">
  <div class="searchbar">
    <div class="search-wrap">
      <div class="search-spinner" id="spinner"></div>
      <input type="text" id="searchInput"
             placeholder="🔍  Type to search by vendor, date, amount, status..."
             oninput="onSearchInput(this.value)" autocomplete="off">
      <button class="clear-btn" id="clearBtn" onclick="clearSearch()">✕</button>
    </div>
  </div>
  <div class="search-hint">
    Results filter automatically after you stop typing —
    <b>no need to press Enter.</b>
  </div>
  <div class="result-count" id="resultCount"></div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Doc ID</th><th>File Name</th><th>Vendor</th>
          <th>Date</th><th>Amount</th><th>Confidence</th>
          <th>Status</th><th>Uploaded</th>
          <th style="text-align:center;min-width:220px">Actions</th>
        </tr>
      </thead>
      <tbody id="tableBody">
      {% for doc in docs %}
        {% set conf = doc.confidence | float %}
        {% set is_pending = doc.status == 'PENDING' %}
        <tr class="doc-row"
            data-search="{{ (doc.vendor~' '~doc.date~' '~doc.amount~' '~doc.s3Key~' '~doc.status~' '~doc.confidence)|lower }}">
          <td><code style="font-size:11px">{{ doc.documentId[:8] }}...</code></td>
          <td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="{{ doc.s3Key }}">{{ doc.s3Key }}</td>
          <td class="searchable">{{ doc.vendor }}</td>
          <td class="searchable">{{ doc.date }}</td>
          <td><b class="searchable">{{ doc.amount }}</b></td>
          <td>
            <span class="{{ 'conf-low' if conf < 80 else 'conf-high' }}">
              {{ doc.confidence }}% {{ '⚠️' if conf < 80 else '✅' }}
            </span>
          </td>
          <td>
            {% if doc.status == 'APPROVED' %}
              <span class="badge badge-approved">✓ Approved</span>
            {% elif doc.status == 'REJECTED' %}
              <span class="badge badge-rejected">✗ Rejected</span>
              {% if doc.rejectReason %}
                <div style="font-size:11px;color:#842029;margin-top:3px">
                  📝 {{ doc.rejectReason }}
                </div>
              {% endif %}
            {% else %}
              <span class="badge badge-pending">⏳ Pending</span>
            {% endif %}
          </td>
          <td style="font-size:11px;color:#666">
            {{ doc.uploadedAt[:10] if doc.uploadedAt else '-' }}
          </td>
          <td style="text-align:center">
            {% if is_pending %}
              {% if doc.flaggedForReview %}
              <button class="btn btn-view"
                onclick="openModal('{{ doc.documentId }}','{{ doc.s3Key }}','{{ doc.vendor }}','{{ doc.date }}','{{ doc.amount }}','{{ doc.confidence }}','{{ doc.pdfUrl }}')">
                📄 View PDF
              </button><br>
              {% endif %}
              <form method="POST" action="/approve" style="display:inline">
                <input type="hidden" name="id" value="{{ doc.documentId }}">
                <button class="btn btn-approve">✓ Approve</button>
              </form>
              <button class="btn btn-reject"
                onclick="toggleReject('reject-{{ doc.documentId }}', this)">
                ✗ Reject
              </button>
              <div class="reject-inline" id="reject-{{ doc.documentId }}">
                <span class="hint">Please provide a reason before rejecting:</span>
                <form method="POST" action="/reject">
                  <input type="hidden" name="id" value="{{ doc.documentId }}">
                  <textarea name="reason"
                    placeholder="e.g. Wrong vendor / Amount mismatch / Duplicate / Unreadable..."></textarea>
                  <div class="actions">
                    <button class="btn btn-reject" type="submit">✗ Confirm Reject</button>
                    <button class="btn btn-disabled" type="button"
                      onclick="toggleReject('reject-{{ doc.documentId }}', null)">Cancel</button>
                  </div>
                </form>
              </div>
            {% else %}
              <span class="btn btn-disabled">{{ doc.status }}</span>
            {% endif %}
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    <div id="emptyMsg" style="display:none;text-align:center;padding:40px;color:#999">
      No documents match your search.
    </div>
  </div>
</div>

<!-- Modal -->
<div class="modal-overlay" id="pdfModal">
  <div class="modal">
    <div class="modal-header">
      <h3>📄 PDF Review — <span id="modalTitle"></span></h3>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="pdf-meta">
      <span><b>Vendor:</b> <span id="mVendor"></span></span>
      <span><b>Date:</b> <span id="mDate"></span></span>
      <span><b>Amount:</b> <span id="mAmount"></span></span>
      <span><b>Confidence:</b>
        <span id="mConf" style="color:#c0392b;font-weight:bold"></span>%
      </span>
      <span style="color:#856404">⚠️ Verify carefully before approving.</span>
    </div>
    <div class="modal-body">
      <iframe id="pdfFrame" src="" title="Invoice PDF"></iframe>
      <div class="modal-approve">
        <p>✅ Document looks correct?</p>
        <form method="POST" action="/approve" id="modalApproveForm">
          <input type="hidden" name="id" id="modalApproveId">
          <button class="btn btn-approve" style="padding:9px 22px;font-size:13px">
            ✓ Approve Document
          </button>
        </form>
      </div>
      <div class="modal-reject">
        <h4>✗ Reject this document</h4>
        <form method="POST" action="/reject" id="modalRejectForm">
          <input type="hidden" name="id" id="modalRejectId">
          <textarea name="reason"
            placeholder="Enter reason: Wrong vendor / Amount mismatch / Duplicate / Unreadable..."></textarea>
          <div class="actions">
            <button class="btn btn-reject" type="submit"
                    style="padding:8px 20px;font-size:13px">✗ Confirm Reject</button>
            <span class="hint-txt">Reason is saved to the database.</span>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>

<script>
let debounceTimer = null;
function onSearchInput(v) {
  document.getElementById('clearBtn').classList.toggle('visible', v.length > 0);
  document.getElementById('spinner').classList.add('visible');
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    filterTable(v.trim().toLowerCase());
    document.getElementById('spinner').classList.remove('visible');
  }, 600);
}
function filterTable(q) {
  const rows = document.querySelectorAll('.doc-row');
  const rc   = document.getElementById('resultCount');
  let vis = 0;
  rows.forEach(row => {
    const match = !q || row.getAttribute('data-search').includes(q);
    row.style.display = match ? '' : 'none';
    if (match) {
      vis++;
      row.querySelectorAll('.searchable').forEach(cell => {
        const orig = cell.getAttribute('data-original') || cell.textContent;
        cell.setAttribute('data-original', orig);
        cell.innerHTML = q
          ? orig.replace(new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')})`, 'gi'),
                         '<mark class="highlight-text">$1</mark>')
          : orig;
      });
    }
  });
  document.getElementById('emptyMsg').style.display = vis === 0 ? 'block' : 'none';
  if (q) { rc.textContent = `Found ${vis} document(s) matching "${q}"`; rc.classList.add('visible'); }
  else   { rc.classList.remove('visible'); }
}
function clearSearch() {
  const i = document.getElementById('searchInput');
  i.value = ''; i.focus();
  document.getElementById('clearBtn').classList.remove('visible');
  document.getElementById('spinner').classList.remove('visible');
  document.getElementById('resultCount').classList.remove('visible');
  clearTimeout(debounceTimer); filterTable('');
}
function toggleReject(id, btn) {
  const p = document.getElementById(id);
  const open = p.classList.contains('open');
  document.querySelectorAll('.reject-inline.open').forEach(x => x.classList.remove('open'));
  if (!open && btn) { p.classList.add('open'); setTimeout(() => p.querySelector('textarea').focus(), 50); }
}
function openModal(docId, s3Key, vendor, date, amount, conf, pdfUrl) {
  document.getElementById('modalTitle').textContent = s3Key;
  document.getElementById('mVendor').textContent    = vendor;
  document.getElementById('mDate').textContent      = date;
  document.getElementById('mAmount').textContent    = amount;
  document.getElementById('mConf').textContent      = conf;
  document.getElementById('modalApproveId').value   = docId;
  document.getElementById('modalRejectId').value    = docId;
  document.getElementById('pdfFrame').src = (pdfUrl && pdfUrl !== 'None' && pdfUrl !== '')
    ? pdfUrl
    : 'data:text/html,<p style="font-family:Arial;padding:40px;color:#888">PDF preview unavailable.</p>';
  document.getElementById('pdfModal').classList.add('active');
}
function closeModal() {
  document.getElementById('pdfModal').classList.remove('active');
  document.getElementById('pdfFrame').src = '';
}
document.getElementById('pdfModal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});
</script>
'''

# ── UPLOAD PAGE TEMPLATE ───────────────────────────────────────────────────────
UPLOAD_TEMPLATE = BASE_STYLE + '''
<style>
  /* ── Prototype banner ── */
  .proto-banner {
    background: linear-gradient(135deg, #856404, #b8860b);
    color: white; padding: 12px 32px;
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  }
  .proto-banner .icon { font-size: 22px; }
  .proto-banner .text { flex: 1; }
  .proto-banner .text strong { font-size: 14px; display: block; }
  .proto-banner .text span   { font-size: 12px; opacity: 0.9; }
  .proto-tag {
    background: white; color: #856404; font-size: 11px; font-weight: bold;
    padding: 3px 10px; border-radius: 12px; text-transform: uppercase;
    white-space: nowrap;
  }

  /* ── Upload card ── */
  .upload-card {
    background: white; border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.09);
    max-width: 720px; margin: 28px auto; overflow: hidden;
  }
  .upload-card-header {
    background: #1F4E79; color: white; padding: 18px 24px;
    display: flex; align-items: center; gap: 12px;
  }
  .upload-card-header h2 { font-size: 17px; }
  .upload-card-header p  { font-size: 12px; opacity: 0.8; margin-top: 3px; }
  .upload-card-body { padding: 28px 28px 24px; }

  /* ── Limit bar ── */
  .limit-bar {
    display: flex; align-items: center; gap: 14px;
    background: #f8f9fa; border: 1px solid #dee2e6;
    border-radius: 8px; padding: 14px 18px; margin-bottom: 24px;
  }
  .limit-icon { font-size: 28px; }
  .limit-text { flex: 1; }
  .limit-text strong { font-size: 14px; display: block; color: #1F4E79; }
  .limit-text span   { font-size: 12px; color: #666; }
  .limit-slots { display: flex; gap: 8px; }
  .slot {
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; border: 2px solid #dee2e6;
  }
  .slot.used     { background: #d4edda; border-color: #1a7f4b; }
  .slot.empty    { background: #f8f9fa; border-color: #dee2e6; }
  .slot.selected { background: #cfe2ff; border-color: #0d6efd; }

  /* ── Drop zone ── */
  .dropzone {
    border: 3px dashed #b0c4d8; border-radius: 12px;
    padding: 40px 20px; text-align: center;
    background: #f8fbff; cursor: pointer;
    transition: all 0.2s; margin-bottom: 20px;
  }
  .dropzone.dragover { border-color: #1F4E79; background: #e8f0fb; }
  .dropzone.maxed    { border-color: #dc3545; background: #fff5f5; cursor: not-allowed; }
  .dropzone .dz-icon { font-size: 48px; margin-bottom: 12px; display: block; }
  .dropzone h3 { font-size: 16px; color: #1F4E79; margin-bottom: 6px; }
  .dropzone p  { font-size: 13px; color: #888; margin-bottom: 16px; }
  .dropzone .choose-btn {
    padding: 10px 24px; background: #1F4E79; color: white;
    border: none; border-radius: 6px; font-size: 14px;
    cursor: pointer; font-weight: bold;
  }
  .dropzone .choose-btn:disabled {
    background: #ccc; cursor: not-allowed;
  }
  #fileInput { display: none; }

  /* ── File list ── */
  .file-list { margin-bottom: 20px; }
  .file-item {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 14px; background: #f8fbff;
    border: 1px solid #cfe2ff; border-radius: 8px; margin-bottom: 8px;
  }
  .file-item .file-icon { font-size: 24px; flex-shrink: 0; }
  .file-item .file-info { flex: 1; min-width: 0; }
  .file-item .file-name {
    font-size: 13px; font-weight: bold; color: #1F4E79;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .file-item .file-size { font-size: 11px; color: #888; }
  .file-item .remove-btn {
    background: #dc3545; color: white; border: none;
    border-radius: 5px; width: 26px; height: 26px;
    cursor: pointer; font-size: 14px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
  }
  .file-item .progress-bar-wrap {
    height: 4px; background: #dee2e6; border-radius: 4px; margin-top: 6px;
  }
  .file-item .progress-bar {
    height: 100%; background: #1F4E79; border-radius: 4px;
    width: 0; transition: width 0.3s;
  }

  /* ── Error / warning ── */
  .alert { padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 13px; }
  .alert-warn { background: #fff3cd; border: 1px solid #ffc107; color: #664d03; }
  .alert-err  { background: #f8d7da; border: 1px solid #f5c2c7; color: #842029; }
  .alert-ok   { background: #d1e7dd; border: 1px solid #a3cfbb; color: #0f5132; }

  /* ── Upload button ── */
  .upload-btn {
    width: 100%; padding: 14px; background: #1F4E79; color: white;
    border: none; border-radius: 8px; font-size: 15px; font-weight: bold;
    cursor: pointer; transition: background 0.2s;
  }
  .upload-btn:hover:not(:disabled) { background: #163d61; }
  .upload-btn:disabled { background: #ccc; cursor: not-allowed; }

  /* ── Upload progress overlay ── */
  .uploading-overlay {
    display: none; text-align: center; padding: 20px;
  }
  .uploading-overlay.visible { display: block; }
  .uploading-overlay .big-spinner {
    width: 48px; height: 48px; border: 5px solid #e0eaf4;
    border-top-color: #1F4E79; border-radius: 50%;
    animation: spin2 0.8s linear infinite; margin: 0 auto 14px;
  }
  @keyframes spin2 { to { transform: rotate(360deg); } }

  /* ── Recent uploads table ── */
  .recent-card {
    background: white; border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.09);
    max-width: 720px; margin: 0 auto 32px; overflow: hidden;
  }
  .recent-card-header {
    background: #163d61; color: white; padding: 14px 20px;
    font-size: 14px; font-weight: bold;
  }
  .recent-table { width: 100%; border-collapse: collapse; }
  .recent-table th {
    background: #1F4E79; color: white; padding: 10px;
    font-size: 12px; text-align: left;
  }
  .recent-table td {
    padding: 9px 10px; font-size: 12px;
    border-bottom: 1px solid #e0eaf4;
  }
  .recent-table tr:last-child td { border-bottom: none; }
  .recent-table tr:hover td { background: #f5f9ff; }
</style>

<div class="topbar">
  <h1>☁ JusticeArch Document Review Portal</h1>
  <span>AWS Textract + DynamoDB Pipeline</span>
</div>
<div class="tab-bar">
  <a href="/">📋 Review Portal</a>
  <a href="/upload" class="active">📤 Upload PDF</a>
</div>

<!-- Prototype Banner -->
<div class="proto-banner">
  <div class="icon">🧪</div>
  <div class="text">
    <strong>Prototype Mode — Student Lab Assignment (WOA7016 Cloud Computing)</strong>
    <span>
      This system is running on AWS Academy Learner Lab with limited resources and credits.
      To conserve costs, uploads are restricted to a maximum of
      <b>3 PDF files per session.</b>
      Each upload triggers Amazon Textract OCR processing and DynamoDB writes.
    </span>
  </div>
  <span class="proto-tag">⚠️ Not for Production Use</span>
</div>

<div style="padding: 28px 32px;">

  <!-- Flash messages -->
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}
      <div class="alert alert-{{ 'ok' if cat == 'success' else 'err' }}"
           style="max-width:720px;margin:0 auto 18px">
        {{ '✅' if cat == 'success' else '❌' }} {{ msg }}
      </div>
    {% endfor %}
  {% endwith %}

  <!-- Upload Card -->
  <div class="upload-card">
    <div class="upload-card-header">
      <div>
        <h2>📤 Upload Invoice / Contract PDF</h2>
        <p>Files are sent to S3 → processed by Textract → stored in DynamoDB automatically.</p>
      </div>
    </div>
    <div class="upload-card-body">

      <!-- Limit indicator -->
      <div class="limit-bar">
        <div class="limit-icon">📦</div>
        <div class="limit-text">
          <strong>Upload Limit: Maximum 3 PDFs per session</strong>
          <span id="limitSubtext">Select up to 3 PDF files to upload at once.</span>
        </div>
        <div class="limit-slots">
          <div class="slot empty" id="slot1">📄</div>
          <div class="slot empty" id="slot2">📄</div>
          <div class="slot empty" id="slot3">📄</div>
        </div>
      </div>

      <!-- Drop zone -->
      <div class="dropzone" id="dropzone"
           onclick="document.getElementById('fileInput').click()"
           ondragover="onDragOver(event)"
           ondragleave="onDragLeave(event)"
           ondrop="onDrop(event)">
        <span class="dz-icon">☁️</span>
        <h3>Drag & Drop PDF files here</h3>
        <p>or click the button below to browse your computer</p>
        <button class="choose-btn" id="chooseBtn" type="button"
                onclick="event.stopPropagation(); document.getElementById('fileInput').click()">
          Browse Files
        </button>
      </div>
      <input type="file" id="fileInput" accept=".pdf" multiple
             onchange="onFilesSelected(this.files)">

      <!-- Alert area -->
      <div id="alertArea"></div>

      <!-- File list -->
      <div class="file-list" id="fileList"></div>

      <!-- Upload button -->
      <div id="uploadSection" style="display:none">
        <button class="upload-btn" id="uploadBtn" onclick="doUpload()">
          ☁️ Upload to S3 &amp; Process with Textract
        </button>
      </div>

      <!-- Uploading overlay -->
      <div class="uploading-overlay" id="uploadingOverlay">
        <div class="big-spinner"></div>
        <p style="font-size:15px;font-weight:bold;color:#1F4E79">Uploading to S3...</p>
        <p style="font-size:13px;color:#888;margin-top:6px">
          Lambda will trigger Textract automatically. Check the Review Portal tab in ~10 seconds.
        </p>
      </div>

    </div>
  </div>

  <!-- Recent uploads -->
  <div class="recent-card">
    <div class="recent-card-header">🕒 Recently Processed Documents (last 5)</div>
    <table class="recent-table">
      <thead>
        <tr>
          <th>File Name</th><th>Vendor</th><th>Amount</th>
          <th>Confidence</th><th>Status</th><th>Uploaded</th>
        </tr>
      </thead>
      <tbody>
      {% for doc in recent %}
        {% set conf = doc.confidence | float %}
        <tr>
          <td title="{{ doc.s3Key }}"
              style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            {{ doc.s3Key }}
          </td>
          <td>{{ doc.vendor }}</td>
          <td>{{ doc.amount }}</td>
          <td>
            <span class="{{ 'conf-low' if conf < 80 else 'conf-high' }}">
              {{ doc.confidence }}% {{ '⚠️' if conf < 80 else '✅' }}
            </span>
          </td>
          <td>
            {% if doc.status == 'APPROVED' %}
              <span class="badge badge-approved">✓ Approved</span>
            {% elif doc.status == 'REJECTED' %}
              <span class="badge badge-rejected">✗ Rejected</span>
            {% else %}
              <span class="badge badge-pending">⏳ Pending</span>
            {% endif %}
          </td>
          <td>{{ doc.uploadedAt[:16] if doc.uploadedAt else '-' }}</td>
        </tr>
      {% endfor %}
      {% if not recent %}
        <tr><td colspan="6" style="text-align:center;padding:20px;color:#999">
          No documents processed yet.
        </td></tr>
      {% endif %}
      </tbody>
    </table>
  </div>

</div>

<script>
const MAX_FILES = {{ max_uploads }};
let selectedFiles = [];

function showAlert(msg, type) {
  document.getElementById('alertArea').innerHTML =
    `<div class="alert alert-${type}" style="margin-bottom:16px">${msg}</div>`;
}
function clearAlert() {
  document.getElementById('alertArea').innerHTML = '';
}

function updateSlots() {
  const icons = ['slot1','slot2','slot3'];
  icons.forEach((id, i) => {
    const el = document.getElementById(id);
    el.className = 'slot ' + (i < selectedFiles.length ? 'selected' : 'empty');
    el.textContent = i < selectedFiles.length ? '📋' : '📄';
  });

  const sub = document.getElementById('limitSubtext');
  const dz  = document.getElementById('dropzone');
  const btn = document.getElementById('chooseBtn');
  const remaining = MAX_FILES - selectedFiles.length;

  if (selectedFiles.length >= MAX_FILES) {
    sub.textContent   = '✋ Maximum reached (3 files, 10 MB each). Remove a file to add another.';
    sub.style.color   = '#c0392b';
    dz.classList.add('maxed');
    btn.disabled = true;
  } else {
    sub.textContent = `${remaining} slot(s) remaining.`;
    sub.style.color = '';
    dz.classList.remove('maxed');
    btn.disabled = false;
  }
}

function renderFileList() {
  const list = document.getElementById('fileList');
  const sect = document.getElementById('uploadSection');
  list.innerHTML = '';

  selectedFiles.forEach((file, idx) => {
    const size = (file.size / 1024).toFixed(1) + ' KB';
    const div  = document.createElement('div');
    div.className = 'file-item';
    div.id = `file-item-${idx}`;
    div.innerHTML = `
      <div class="file-icon">📄</div>
      <div class="file-info">
        <div class="file-name">${file.name}</div>
        <div class="file-size">${size} • PDF</div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" id="prog-${idx}"></div>
        </div>
      </div>
      <button class="remove-btn" onclick="removeFile(${idx})">✕</button>
    `;
    list.appendChild(div);
  });

  sect.style.display = selectedFiles.length > 0 ? 'block' : 'none';
  updateSlots();
}

function addFiles(files) {
  clearAlert();
  let added = 0;
  for (const file of files) {
    if (selectedFiles.length >= MAX_FILES) {
      showAlert(`⚠️ Maximum ${MAX_FILES} PDFs allowed per upload session. Extra files were ignored.`, 'warn');
      break;
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showAlert(`❌ "${file.name}" is not a PDF. Only .pdf files are accepted.`, 'err');
      continue;
    }
    if (file.size > 10 * 1024 * 1024) {
      showAlert(`❌ "${file.name}" exceeds 10MB limit.`, 'err');
      continue;
    }
    selectedFiles.push(file);
    added++;
  }
  renderFileList();
}

function removeFile(idx) {
  selectedFiles.splice(idx, 1);
  clearAlert();
  renderFileList();
}

function onFilesSelected(files) { addFiles(Array.from(files)); }

function onDragOver(e) {
  e.preventDefault();
  if (selectedFiles.length < MAX_FILES)
    document.getElementById('dropzone').classList.add('dragover');
}
function onDragLeave(e) {
  document.getElementById('dropzone').classList.remove('dragover');
}
function onDrop(e) {
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('dragover');
  if (selectedFiles.length < MAX_FILES) addFiles(Array.from(e.dataTransfer.files));
}

async function doUpload() {
  if (selectedFiles.length === 0) return;

  document.getElementById('uploadBtn').disabled = true;
  document.getElementById('uploadingOverlay').classList.add('visible');
  document.getElementById('uploadSection').style.display = 'none';

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append('files', f));

  try {
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    const data = await resp.json();
    if (data.success) {
      window.location.href = '/upload?uploaded=' + data.count;
    } else {
      showAlert('❌ Upload failed: ' + (data.error || 'Unknown error'), 'err');
      document.getElementById('uploadBtn').disabled = false;
      document.getElementById('uploadingOverlay').classList.remove('visible');
      document.getElementById('uploadSection').style.display = 'block';
    }
  } catch(err) {
    showAlert('❌ Network error. Please try again.', 'err');
    document.getElementById('uploadBtn').disabled = false;
    document.getElementById('uploadingOverlay').classList.remove('visible');
    document.getElementById('uploadSection').style.display = 'block';
  }
}

// Show success message after redirect
const params = new URLSearchParams(window.location.search);
if (params.get('uploaded')) {
  const n = params.get('uploaded');
  const a = document.getElementById('alertArea');
  a.innerHTML = `<div class="alert alert-ok" style="margin-bottom:16px">
    ✅ Successfully uploaded ${n} PDF file(s) to S3.
    Lambda is now processing with Textract — check the
    <a href="/" style="color:#0f5132;font-weight:bold">Review Portal</a>
    in ~10 seconds.
  </div>`;
}
</script>
'''

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    docs  = get_all_docs()
    stats = calc_stats(docs)
    return render_template_string(REVIEW_TEMPLATE, docs=docs, **stats)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        files = request.files.getlist('files')

        # Enforce max 3
        if len(files) >= MAX_UPLOADS:
            files = files[:MAX_UPLOADS]

        uploaded = 0
        errors   = []
        for f in files:
            if not f.filename:
                continue
            filename = secure_filename(f.filename)
            if not filename.lower().endswith('.pdf'):
                errors.append(f'{filename} is not a PDF')
                continue
            try:
                s3_client.upload_fileobj(
                    f,
                    BUCKET_NAME,
                    filename,
                    ExtraArgs={'ContentType': 'application/pdf'}
                )
                uploaded += 1
            except ClientError as e:
                errors.append(f'Failed to upload {filename}: {str(e)}')

        if uploaded > 0:
            return jsonify({'success': True, 'count': uploaded})
        else:
            return jsonify({'success': False, 'error': '; '.join(errors)}), 400

    # GET — show upload page
    all_docs = get_all_docs()
    # Sort by uploadedAt descending, take last 5
    sorted_docs = sorted(
        all_docs,
        key=lambda d: d.get('uploadedAt', ''),
        reverse=True
    )[:5]
    return render_template_string(
        UPLOAD_TEMPLATE,
        recent=sorted_docs,
        max_uploads=MAX_UPLOADS
    )

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
    reason = request.form.get('reason', 'No reason provided').strip() or 'No reason provided'
    table.update_item(
        Key={'documentId': doc_id},
        UpdateExpression='SET #s = :v, rejectReason = :r, flaggedForReview = :f',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':v': 'REJECTED', ':r': reason, ':f': False}
    )
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)