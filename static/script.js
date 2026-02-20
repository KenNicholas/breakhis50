document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    
    // Upload area click
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#764ba2';
        uploadArea.style.background = '#f8f9ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = 'white';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
        uploadArea.style.background = 'white';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    // Handle file upload and prediction
    async function handleFile(file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!validTypes.includes(file.type)) {
            showError('Please upload a valid image file (PNG, JPG, JPEG)');
            return;
        }
        
        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            showError('File size must be less than 16MB');
            return;
        }
        
        // Show loading
        loading.style.display = 'block';
        results.style.display = 'none';
        error.style.display = 'none';
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            // PENTING: GANTI URL INI SESUAI DOMAIN VERCEL ANDA
            const API_URL = '/api/predict';  // Relative URL untuk Vercel
            
            const response = await fetch(API_URL, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                displayResults(data);
            } else {
                showError(data.error || 'Prediction failed');
            }
        } catch (err) {
            console.error(err);
            showError('Network error. Please try again.');
        } finally {
            loading.style.display = 'none';
        }
    }
    
    // Display results
    function displayResults(data) {
        // Set prediction badge
        const badge = document.getElementById('predictionBadge');
        const label = document.getElementById('predictionLabel');
        const confidence = document.getElementById('confidenceValue');
        
        badge.className = `prediction-badge ${data.prediction.toLowerCase()}`;
        label.textContent = data.prediction;
        confidence.textContent = data.confidence;
        
        // Set probability bars
        const benignProb = data.probabilities.Benign;
        const malignantProb = data.probabilities.Malignant;
        
        document.getElementById('benignProgress').style.width = (benignProb * 100) + '%';
        document.getElementById('malignantProgress').style.width = (malignantProb * 100) + '%';
        document.getElementById('benignValue').textContent = benignProb.toFixed(4);
        document.getElementById('malignantValue').textContent = malignantProb.toFixed(4);
        
        // Show results
        results.style.display = 'block';
    }
    
    // Show error
    function showError(message) {
        errorMessage.textContent = message;
        error.style.display = 'block';
        loading.style.display = 'none';
        results.style.display = 'none';
    }
});