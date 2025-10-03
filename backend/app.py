from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from features import extract_url_features  # Our feature extractor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow requests from extension (localhost for dev)

# Load the trained XGBoost model (copy xgboost_phishing_model.pkl here first!)
try:
    model = joblib.load('xgboost_phishing_model.pkl')
    print("XGBoost model loaded—ready to block phishers!")
except FileNotFoundError:
    print("ERROR: xgboost_phishing_model.pkl not found! Copy from upload/Model Training/ folder.")
    model = None

@app.route('/check', methods=['POST'])
def check_phishing():
    if model is None:
        return jsonify({'error': 'Model not loaded—check backend setup'}), 500
    
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'No URL provided—send one from the extension!'}), 400
    
    # Extract features and predict
    features_df = extract_url_features(url)
    prediction = model.predict(features_df)[0]
    probabilities = model.predict_proba(features_df)[0]
    confidence = float(max(probabilities))  # Force plain float—no numpy!
    
    # Dataset: 1 = legit/safe, -1 = phishing/unsafe
    is_safe = bool(int(prediction) == 1)  # Strip numpy, convert to plain Python bool (fixes serialization!)
    
    # Quick log for debugging (MongoDB next week)
    print(f"🔍 URL: {url} | Safe: {is_safe} | Confidence: {confidence:.2f}")
    
    return jsonify({
        'isSafe': is_safe,  # Plain True/False—JSON serializes perfectly!
        'confidence': confidence,  # Plain float for JS
        'riskScore': float(1 - confidence) if not is_safe else 0.0  # UI hook: Higher = riskier
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Phishing detector online—extension blocks incoming!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)