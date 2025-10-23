from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
from features import extract_url_features, categorize_website, extract_page_text, advanced_text_preprocessing, create_advanced_features

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

# Load optional category model
try:
    # Try to load advanced model first
    with open("pickle/category_model_advanced.pkl", "rb") as f:
        category_model_data = pickle.load(f)
        category_model = category_model_data['ensemble_model']
        category_tfidf = category_model_data['tfidf_vectorizer']
        category_label_encoder = category_model_data['label_encoder']
        category_feature_columns = category_model_data['feature_columns']
        category_feature_selector = category_model_data.get('feature_selector', None)
        category_scaler = category_model_data.get('scaler', None)
    print("✅ Advanced category model loaded successfully!")
except Exception as e:
    print(f"ℹ️ Advanced category model not found, trying basic model: {e}")
    try:
        # Fallback to basic model
        with open("pickle/category_model.pkl", "rb") as f:
            category_model = pickle.load(f)
        with open("pickle/category_labels.pkl", "rb") as f:
            category_label_encoder = pickle.load(f)
        category_tfidf = None
        category_feature_columns = None
        print("✅ Basic category model loaded successfully!")
    except Exception as e2:
        print(f"ℹ️ No category model available: {e2}")
        category_model = None
        category_label_encoder = None
        category_tfidf = None
        category_feature_columns = None


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
        # Get category via ML if available, else heuristic
        category = "Unknown"
        category_confidence = 0.0
        
        if category_model is not None and category_label_encoder is not None:
            page_text = extract_page_text(url)
            if page_text and len(page_text) > 50:  # Need meaningful text
                try:
                    if category_tfidf is not None and category_feature_columns is not None:
                        # Advanced model with additional features
                        processed_text = advanced_text_preprocessing(page_text)
                        
                        # Transform text
                        X_text = category_tfidf.transform([processed_text])
                        
                        # Create additional features
                        temp_df = pd.DataFrame({'text': [processed_text]})
                        advanced_features = create_advanced_features(temp_df, 'text')
                        
                        # Combine features
                        import numpy as np
                        X_combined = np.hstack([X_text.toarray(), advanced_features.values])
                        
                        # Apply feature selection and scaling if available
                        if category_feature_selector is not None:
                            X_selected = category_feature_selector.transform(X_combined)
                            if category_scaler is not None:
                                X_final = category_scaler.transform(X_selected)
                            else:
                                X_final = X_selected
                        else:
                            X_final = X_combined
                        
                        # Predict
                        proba = category_model.predict_proba(X_final)[0]
                        cat_pred_idx = int(category_model.predict(X_final)[0])
                        category_confidence = float(proba[cat_pred_idx] * 100)
                        category = category_label_encoder.inverse_transform([cat_pred_idx])[0]
                    else:
                        # Basic model
                        proba = category_model.predict_proba([page_text])[0]
                        cat_pred_idx = int(category_model.predict([page_text])[0])
                        category_confidence = float(proba[cat_pred_idx] * 100)
                        category = category_label_encoder.inverse_transform([cat_pred_idx])[0]
                    
                    # Only use ML prediction if confidence is reasonable
                    if category_confidence < 25.0:
                        category = categorize_website(url)
                        category_confidence = 0.0
                        
                except Exception as e:
                    print(f"ML category prediction failed: {e}")
                    category = categorize_website(url)
                    category_confidence = 0.0
            else:
                category = categorize_website(url)
                category_confidence = 0.0
        else:
            category = categorize_website(url)
            category_confidence = 0.0

        print(f"🔍 URL: {url} | Safe: {is_safe} | Confidence: {confidence:.2f}%")

        return jsonify({
            "status": "Phishing Detected" if is_phishing else "Safe Website",
            "isSafe": is_safe,
            "isPhishing": is_phishing,
            "confidence": round(confidence, 2),
            "riskScore": risk_score,
            "category": category,
            "categoryConfidence": round(category_confidence, 2)
        })

    except Exception as e:
        print(f"❌ Error analyzing URL {url}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Phishing detection backend running ✅"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
