from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
from features import extract_url_features

app = Flask(__name__)
CORS(app)

# Load the trained model
try:
    with open("pickle/model.pkl", "rb") as f:
        model = pickle.load(f)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None


@app.route("/check", methods=["POST"])
def check_phishing():
    if model is None:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # Extract features
        features_df = extract_url_features(url)

        # Predict using model
        prediction = int(model.predict(features_df)[0])
        probabilities = model.predict_proba(features_df)[0]
        confidence = float(probabilities[prediction] * 100)
        risk_score = round(100 - confidence, 2)

        # Interpret results
        is_safe = True if prediction == 1 else False
        is_phishing = not is_safe

        print(f"🔍 URL: {url} | Safe: {is_safe} | Confidence: {confidence:.2f}%")

        return jsonify({
            "status": "Phishing Detected" if is_phishing else "Safe Website",
            "isSafe": is_safe,
            "isPhishing": is_phishing,
            "confidence": round(confidence, 2),
            "riskScore": risk_score
        })

    except Exception as e:
        print(f"❌ Error analyzing URL {url}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Phishing detection backend running ✅"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
