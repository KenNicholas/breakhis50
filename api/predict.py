import os
import base64
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import io
from PIL import Image
import sys
import traceback

# Inisialisasi Flask app
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
CORS(app)

# Logging untuk debug
print("=== APP STARTING ===", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)

# Konfigurasi Hugging Face
HF_TOKEN = os.environ.get('HF_TOKEN', '')
API_URL = "https://api-inference.huggingface.co/models/KenNicholas/breast-cancer-resnet50-gradcam"  # GANTI DENGAN USERNAME ANDA!

print(f"HF_TOKEN exists: {'Yes' if HF_TOKEN else 'No'}", file=sys.stderr)
print(f"API_URL: {API_URL}", file=sys.stderr)

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    """Home page"""
    print("Index route called", file=sys.stderr)
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error in index: {str(e)}", file=sys.stderr)
        return jsonify({'error': 'Template not found'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction request via Hugging Face API"""
    print("Predict route called", file=sys.stderr)
    
    if 'file' not in request.files:
        print("No file in request", file=sys.stderr)
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        print("Empty filename", file=sys.stderr)
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Baca file gambar
        print(f"Reading file: {file.filename}", file=sys.stderr)
        image_bytes = file.read()
        print(f"File size: {len(image_bytes)} bytes", file=sys.stderr)
        
        # Cek token
        if not HF_TOKEN:
            print("HF_TOKEN not set", file=sys.stderr)
            return jsonify({'error': 'HF_TOKEN not configured'}), 500
        
        # Kirim ke Hugging Face API
        print("Calling Hugging Face API...", file=sys.stderr)
        response = requests.post(
            API_URL,
            headers=headers,
            data=image_bytes,
            timeout=30
        )
        
        print(f"HF API Response status: {response.status_code}", file=sys.stderr)
        
        if response.status_code != 200:
            print(f"HF API Error: {response.text}", file=sys.stderr)
            return jsonify({'error': f'Hugging Face API error: {response.text}'}), 500
        
        result = response.json()
        print(f"HF API Result: {json.dumps(result)[:200]}...", file=sys.stderr)
        
        # Parse hasil dari Hugging Face
        if isinstance(result, list) and len(result) > 0:
            predictions = result[0] if isinstance(result[0], list) else result
            
            # Cari prediksi dengan score tertinggi
            top_pred = max(predictions, key=lambda x: x['score'])
            pred_class = top_pred['label'].upper()
            confidence = top_pred['score']
            
            # Dapatkan probabilitas untuk kedua kelas
            prob_benign = 0.0
            prob_malignant = 0.0
            
            for pred in predictions:
                if pred['label'].upper() == 'BENIGN':
                    prob_benign = pred['score']
                elif pred['label'].upper() == 'MALIGNANT':
                    prob_malignant = pred['score']
            
            # Jika hanya satu kelas yang keluar
            if prob_benign == 0 and prob_malignant == 0:
                if pred_class == 'BENIGN':
                    prob_benign = confidence
                    prob_malignant = 1 - confidence
                else:
                    prob_malignant = confidence
                    prob_benign = 1 - confidence
            
            print(f"Prediction: {pred_class}, Confidence: {confidence}", file=sys.stderr)
            
            return jsonify({
                'success': True,
                'prediction': pred_class,
                'confidence': f'{confidence:.2%}',
                'probabilities': {
                    'Benign': float(prob_benign),
                    'Malignant': float(prob_malignant)
                }
            })
        else:
            print(f"Unexpected response format: {result}", file=sys.stderr)
            return jsonify({'error': 'Unexpected API response format'}), 500
        
    except requests.exceptions.Timeout:
        print("HF API timeout", file=sys.stderr)
        return jsonify({'error': 'Hugging Face API timeout'}), 504
    except Exception as e:
        print(f"Error in predict: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': str(e)}), 500

# Untuk Vercel serverless
def handler(event, context):
    return app(event, context)

# Untuk development lokal
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)