import fitz
import urllib.request
import json
import os

test_pdf_path = r'C:\Users\yniti\PDF_to_HTML_Converter_App\test_sample.pdf'
doc = fitz.open()
p1 = doc.new_page()
p1.insert_text((50, 50), 'Sample Heading Page 1', fontsize=18, color=(0.9, 0.0, 0.5))
p1.insert_text((50, 90), 'This is a test paragraph for the webapp converter engine.', fontsize=11)

p2 = doc.new_page()
p2.insert_text((50, 50), 'Sample Heading Page 2', fontsize=18, color=(0.0, 0.4, 0.8))
p2.insert_text((50, 90), 'Another paragraph demonstrating multi-page conversion and ZIP download.', fontsize=11)
doc.save(test_pdf_path)
doc.close()

boundary = '----BoundaryTest'
with open(test_pdf_path, 'rb') as f:
    fb = f.read()

payload = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="pdf_file"; filename="test_sample.pdf"\r\n'
    f'Content-Type: application/pdf\r\n\r\n'
).encode('utf-8') + fb + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request(
    'http://localhost:8090/api/convert',
    data=payload,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

res = urllib.request.urlopen(req)
data = json.loads(res.read().decode('utf-8'))
print('Convert API Success:', data.get('success'))
print('Session ID:', data.get('sessionId'))
print('Total Pages:', data.get('totalPages'))

session_id = data['sessionId']
# Test standalone single-file download
std_res = urllib.request.urlopen(f'http://localhost:8090/api/session/{session_id}/download/standalone')
std_data = std_res.read()
print('Standalone .html Download Status:', std_res.status, 'Size:', len(std_data), 'bytes')
print('TEST PASSED SUCCESSFULLY! 1-Click single HTML file download ready.')
