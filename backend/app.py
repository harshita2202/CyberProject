from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from features import extract_url_features  # Our feature extractor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow requests from extension (localhost for dev)

# Load trained XGBoost model
model = joblib.load('xgboost_phishing_model.pkl')

@app.route('/check', methods=['POST'])
def check_phishing():
    if model is None:
        return jsonify({'error': 'Model not loaded—check backend setup'}), 500
    
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'No URL provided—send one from the extension!'}), 400
    
    # Extract features for the URL
    features_df = extract_url_features(url)
    
    # Predict 0 or 1
    prediction = int(model.predict(features_df)[0])
    
    # Get probability/confidence
    probabilities = model.predict_proba(features_df)[0]  # [prob_0, prob_1]
    confidence = float(probabilities[prediction] * 100)  # Convert to percentage
    
    # Determine safe vs phishing
    is_phishing = True if prediction == 1 else False
    is_safe = not is_phishing
    
    # Log for debugging
    print(f"🔍 URL: {url} | Safe: {is_safe} | Phishing: {is_phishing} | Confidence: {confidence:.2f}%")
    
    return jsonify({
        'isSafe': is_safe,              # True/False
        'isPhishing': is_phishing,      # True/False
        'confidence': round(confidence, 2)  # Percentage with 2 decimals
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Phishing detector online!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
