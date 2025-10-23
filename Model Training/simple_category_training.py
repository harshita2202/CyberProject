import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
import numpy as np
import re

def simple_text_preprocessing(text):
    """Simple text preprocessing for category classification."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs, emails, phone numbers
    text = re.sub(r'http[s]?://\S+', ' ', text)
    text = re.sub(r'\S+@\S+', ' ', text)
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', ' ', text)
    
    # Remove special characters but keep important punctuation
    text = re.sub(r'[^\w\s\.\,\!\?]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def create_simple_features(df, text_col):
    """Create simple features from text for classification."""
    features = []
    
    for text in df[text_col]:
        text = str(text)
        
        # Basic text features
        word_count = len(text.split())
        char_count = len(text)
        avg_word_length = char_count / max(word_count, 1)
        
        # Simple keyword features
        tech_keywords = ['software', 'technology', 'computer', 'digital', 'app', 'system', 'data', 'tech']
        business_keywords = ['business', 'company', 'corporate', 'enterprise', 'management', 'finance']
        ecommerce_keywords = ['shop', 'buy', 'sell', 'store', 'product', 'price', 'cart', 'order']
        education_keywords = ['education', 'learn', 'course', 'student', 'school', 'university', 'study']
        news_keywords = ['news', 'article', 'report', 'update', 'breaking', 'latest', 'story']
        
        tech_score = sum(1 for word in tech_keywords if word in text.lower())
        business_score = sum(1 for word in business_keywords if word in text.lower())
        ecommerce_score = sum(1 for word in ecommerce_keywords if word in text.lower())
        education_score = sum(1 for word in education_keywords if word in text.lower())
        news_score = sum(1 for word in news_keywords if word in text.lower())
        
        features.append({
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'tech_score': tech_score,
            'business_score': business_score,
            'ecommerce_score': ecommerce_score,
            'education_score': education_score,
            'news_score': news_score
        })
    
    return pd.DataFrame(features)

# Load and preprocess data
print("🚀 Training SIMPLE website category model...")
cat_df = pd.read_csv("website_classification.csv")

text_col = "cleaned_website_text"
cat_df = cat_df.dropna(subset=[text_col, "Category"]).reset_index(drop=True)
cat_df[text_col] = cat_df[text_col].apply(simple_text_preprocessing)

# Remove very short text
cat_df = cat_df[cat_df[text_col].str.len() >= 50].reset_index(drop=True)

# Remove categories with too few samples
category_counts = cat_df["Category"].value_counts()
valid_categories = category_counts[category_counts >= 10].index
cat_df = cat_df[cat_df["Category"].isin(valid_categories)].reset_index(drop=True)

print(f"📊 Final dataset: {len(cat_df)} samples, {len(valid_categories)} categories")

# Create simple features
print("🔧 Creating simple features...")
simple_features = create_simple_features(cat_df, text_col)

# Encode labels
label_encoder = LabelEncoder()
y_cat = label_encoder.fit_transform(cat_df["Category"])

# Simple TF-IDF
tfidf = TfidfVectorizer(
    max_features=10000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.9,
    stop_words='english'
)

# Transform text
X_text = tfidf.fit_transform(cat_df[text_col])

# Combine text and simple features
X_combined = np.hstack([X_text.toarray(), simple_features.values])

print(f"📊 Features: {X_combined.shape[1]}")

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_combined, y_cat, test_size=0.2, random_state=42, stratify=y_cat
)

# Create simple Random Forest model
print("🎯 Training simple Random Forest model...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

# Train model
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

final_accuracy = metrics.accuracy_score(y_test, y_pred)
final_f1 = metrics.f1_score(y_test, y_pred, average='weighted')

print(f"\n🎉 FINAL MODEL PERFORMANCE:")
print(f"Accuracy: {final_accuracy:.3f}")
print(f"F1 Score: {final_f1:.3f}")

if final_accuracy >= 0.85:
    print("🎯 EXCELLENT! 85%+ accuracy achieved!")
elif final_accuracy >= 0.75:
    print("🔥 Good performance! 75%+ accuracy achieved.")
else:
    print("📈 Decent performance, can be improved with more data.")

# Detailed classification report
print("\n📊 Per-category performance:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Save the model
os.makedirs("pickle", exist_ok=True)

model_data = {
    'ensemble_model': model,
    'tfidf_vectorizer': tfidf,
    'label_encoder': label_encoder,
    'feature_columns': simple_features.columns.tolist(),
    'feature_selector': None,
    'scaler': None,
    'accuracy': final_accuracy
}

with open("pickle/category_model_advanced.pkl", "wb") as f:
    pickle.dump(model_data, f)

print("💾 Saved simple category model as category_model_advanced.pkl")
