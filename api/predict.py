import os
import base64
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import io
from PIL import Image

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
CORS(app)

HF_TOKEN = os.environ.get('HF_TOKEN', '')  
API_URL = "https://api-inference.huggingface.co/models/Ken2707/breakhis-resnet50"  # GANTI!

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Handle prediction request via Hugging Face API"""
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Baca file gambar
        image_bytes = file.read()
        
        # Kirim ke Hugging Face API
        response = requests.post(
            API_URL,
            headers=headers,
            data=image_bytes,
            timeout=30
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'Hugging Face API error: {response.text}'}), 500
        
        result = response.json()
        
        # Parse hasil dari Hugging Face
        # Format response HF biasanya: [[{"label": "MALIGNANT", "score": 0.99}, ...]]
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
            return jsonify({'error': 'Unexpected API response format'}), 500
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Hugging Face API timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Untuk Vercel serverless
def handler(event, context):
    return app(event, context)

# Untuk development lokal
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)