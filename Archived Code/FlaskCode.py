from flask import Flask, render_template_string, request, redirect
import boto3

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('JusticeArchDocuments')

TEMPLATE = '''
<!DOCTYPE html><html><head><title>JusticeArch Review Portal</title>
<style>body{font-family:Arial;margin:40px;background:#f4f8fb}
table{border-collapse:collapse;width:100%}
th{background:#1F4E79;color:white;padding:10px}
td{border:1px solid #ccc;padding:8px}
tr:nth-child(even){background:#eaf1fb}
.flag{color:red;font-weight:bold}</style></head>
<body><h1>JusticeArch Document Review Portal</h1>
<form method=GET action=/search>
<input name=q placeholder='Search keyword...'> <button>Search</button></form>
<br><table><tr><th>ID</th><th>S3 Key</th><th>Vendor</th>
<th>Date</th><th>Amount</th><th>Confidence</th><th>Status</th><th>Action</th></tr>
{% for doc in docs %}<tr>
<td>{{ doc.documentId[:8] }}</td><td>{{ doc.s3Key }}</td>
<td>{{ doc.vendor }}</td><td>{{ doc.date }}</td><td>{{ doc.amount }}</td>
<td class='{{ "flag" if doc.flaggedForReview else "" }}'>
{{ doc.confidence }}%</td><td>{{ doc.status }}</td>
<td><form method=POST action=/approve>
<input type=hidden name=id value={{ doc.documentId }}>
<button>Approve</button></form></td></tr>{% endfor %}
</table></body></html>'''

@app.route('/')
def index():
    result = table.scan(
        FilterExpression='flaggedForReview = :t',
        ExpressionAttributeValues={':t': True}
    )
    return render_template_string(TEMPLATE, docs=result['Items'])

@app.route('/search')
def search():
    q = request.args.get('q', '')
    result = table.scan()
    docs = [d for d in result['Items']
            if q.lower() in str(d).lower()]
    return render_template_string(TEMPLATE, docs=docs)

@app.route('/approve', methods=['POST'])
def approve():
    doc_id = request.form['id']
    table.update_item(
        Key={'documentId': doc_id},
        UpdateExpression='SET #s = :v',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':v': 'APPROVED'}
    )
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)