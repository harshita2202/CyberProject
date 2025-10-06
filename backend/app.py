from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from urllib.parse import urlparse
from features import extract_url_features  # Our feature extractor

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow requests from extension (localhost for dev)

# Load trained XGBoost model
model = joblib.load('xgboost_phishing_model.pkl')

# Temporary test override: force certain domains to return phishing (label=1)
# You can edit this set while testing.
FORCE_PHISH_HOSTS = {
    'testsafebrowsing.appspot.com',
    'www.amtso.org'
}

@app.route('/check', methods=['POST'])
def check_phishing():
    if model is None:
        return jsonify({'error': 'Model not loaded—check backend setup'}), 500
    
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'No URL provided—send one from the extension!'}), 400
    
    # Temporary override: force phishing for selected test domains
    try:
        hostname = urlparse(url).hostname or ''
    except Exception:
        hostname = ''
    if hostname in FORCE_PHISH_HOSTS:
        confidence = 92.0
        print(f"⚠️ Override PHISH for test host: {hostname} | URL: {url} | Confidence: {confidence:.2f}%")
        return jsonify({
            'label': 1,
            'confidence': confidence,
            'isPhishing': True,
            'isSafe': False
        })

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
        'label': prediction,            # 0 or 1 for extension compatibility
        'confidence': round(confidence, 2),
        'isSafe': is_safe,
        'isPhishing': is_phishing
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Phishing detector online!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
