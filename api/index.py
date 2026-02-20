from http.server import BaseHTTPRequestHandler
import json
import os
import requests
from urllib.parse import parse_qs
import base64
from io import BytesIO

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Kirim HTML sederhana
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Breast Cancer Detection</title>
                <style>
                    body { font-family: Arial; text-align: center; margin: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                    .container { max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 20px; color: #333; }
                    .upload-btn { background: #667eea; color: white; padding: 12px 30px; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; }
                    #result { margin-top: 20px; padding: 20px; border-radius: 10px; }
                    .benign { background: #4CAF50; color: white; }
                    .malignant { background: #F44336; color: white; }
                </style>
            </head>
            <body>
                <h1>🔬 Breast Cancer Detection</h1>
                <p>ResNet50 + Grad-CAM</p>
                <p>Kelompok 8 | BreakHis 400X</p>
                
                <div class="container">
                    <h2>Upload Histopathology Image</h2>
                    <input type="file" id="imageInput" accept="image/*">
                    <br><br>
                    <button class="upload-btn" onclick="predict()">Analyze</button>
                    
                    <div id="result" style="display:none;"></div>
                </div>

                <script>
                    async function predict() {
                        const file = document.getElementById('imageInput').files[0];
                        if (!file) {
                            alert('Please select an image');
                            return;
                        }

                        const resultDiv = document.getElementById('result');
                        resultDiv.style.display = 'block';
                        resultDiv.innerHTML = 'Analyzing...';
                        resultDiv.className = '';

                        const formData = new FormData();
                        formData.append('file', file);

                        try {
                            const response = await fetch('/api/predict', {
                                method: 'POST',
                                body: formData
                            });
                            
                            const data = await response.json();
                            
                            if (data.success) {
                                resultDiv.innerHTML = `
                                    <h3>Prediction: ${data.prediction}</h3>
                                    <p>Confidence: ${data.confidence}</p>
                                    <p>Benign: ${(data.probabilities.Benign * 100).toFixed(2)}%</p>
                                    <p>Malignant: ${(data.probabilities.Malignant * 100).toFixed(2)}%</p>
                                `;
                                resultDiv.className = data.prediction.toLowerCase();
                            } else {
                                resultDiv.innerHTML = 'Error: ' + data.error;
                            }
                        } catch (error) {
                            resultDiv.innerHTML = 'Error: ' + error.message;
                        }
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/predict':
            try:
                # Baca content length
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Parse multipart form data
                boundary = self.headers['Content-Type'].split('=')[1].encode()
                parts = post_data.split(b'--' + boundary)
                
                # Cari file
                image_data = None
                for part in parts:
                    if b'filename="' in part:
                        # Skip headers
                        image_data = part.split(b'\r\n\r\n')[1].split(b'\r\n--')[0]
                        break
                
                if not image_data:
                    raise Exception('No file found')
                
                # Panggil Hugging Face API
                HF_TOKEN = os.environ.get('HF_TOKEN', '')
                API_URL = "https://api-inference.huggingface.co/models/KenNicholas/breast-cancer-resnet50-gradcam"
                
                headers = {"Authorization": f"Bearer {HF_TOKEN}"}
                
                response = requests.post(
                    API_URL,
                    headers=headers,
                    data=image_data,
                    timeout=30
                )
                
                if response.status_code != 200:
                    raise Exception(f'HF API error: {response.text}')
                
                result = response.json()
                
                # Parse result
                if isinstance(result, list) and len(result) > 0:
                    predictions = result[0] if isinstance(result[0], list) else result
                    top_pred = max(predictions, key=lambda x: x['score'])
                    
                    pred_class = top_pred['label'].upper()
                    confidence = top_pred['score']
                    
                    prob_benign = next((p['score'] for p in predictions if p['label'].upper() == 'BENIGN'), 0)
                    prob_malignant = next((p['score'] for p in predictions if p['label'].upper() == 'MALIGNANT'), 0)
                    
                    if prob_benign == 0 and prob_malignant == 0:
                        if pred_class == 'BENIGN':
                            prob_benign = confidence
                            prob_malignant = 1 - confidence
                        else:
                            prob_malignant = confidence
                            prob_benign = 1 - confidence
                    
                    response_data = {
                        'success': True,
                        'prediction': pred_class,
                        'confidence': f'{confidence:.2%}',
                        'probabilities': {
                            'Benign': prob_benign,
                            'Malignant': prob_malignant
                        }
                    }
                else:
                    response_data = {'success': False, 'error': 'Unexpected API response'}
                
                # Kirim response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()