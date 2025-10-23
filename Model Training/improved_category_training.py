import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn import metrics
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_selection import SelectKBest, chi2
import numpy as np
import re
from collections import Counter

def advanced_text_preprocessing(text):
    """Enhanced text preprocessing with better cleaning."""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs but keep domain keywords
    text = re.sub(r'http[s]?://(?:www\.)?', ' ', text)
    text = re.sub(r'\.com|\.org|\.net|\.edu|\.gov', ' ', text)
    
    # Remove emails but keep @mentions
    text = re.sub(r'\S+@\S+\.\S+', ' ', text)
    
    # Remove phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', ' ', text)
    
    # Remove hex colors and codes
    text = re.sub(r'#[0-9a-f]{3,6}\b', ' ', text)
    
    # Keep alphanumeric and important punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-]', ' ', text)
    
    # Remove standalone numbers but keep alphanumeric
    text = re.sub(r'\b\d+\b', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

def create_enhanced_features(df, text_col):
    """Create comprehensive features from text for better classification."""
    features = []
    
    for text in df[text_col]:
        text = str(text)
        words = text.lower().split()
        
        # Basic text statistics
        word_count = len(words)
        char_count = len(text)
        avg_word_length = char_count / max(word_count, 1)
        unique_words = len(set(words))
        unique_ratio = unique_words / max(word_count, 1)
        
        # Sentence and structure features
        sentence_count = max(1, text.count('.') + text.count('!') + text.count('?'))
        avg_sentence_length = word_count / sentence_count
        
        # Punctuation features
        exclamation_count = text.count('!')
        question_count = text.count('?')
        comma_count = text.count(',')
        
        # Enhanced domain-specific keywords
        tech_keywords = ['software', 'technology', 'computer', 'digital', 'app', 'application',
                        'system', 'data', 'tech', 'code', 'programming', 'developer', 'api',
                        'cloud', 'server', 'database', 'algorithm', 'ai', 'machine learning']
        
        business_keywords = ['business', 'company', 'corporate', 'enterprise', 'management',
                           'finance', 'investment', 'profit', 'revenue', 'market', 'industry',
                           'strategy', 'consulting', 'service', 'solution', 'professional']
        
        ecommerce_keywords = ['shop', 'buy', 'sell', 'store', 'product', 'price', 'cart',
                             'order', 'purchase', 'shipping', 'delivery', 'discount', 'sale',
                             'customer', 'payment', 'checkout', 'wishlist', 'inventory']
        
        education_keywords = ['education', 'learn', 'learning', 'course', 'student', 'school',
                            'university', 'study', 'teach', 'teaching', 'training', 'lesson',
                            'tutorial', 'class', 'exam', 'degree', 'academic', 'research']
        
        news_keywords = ['news', 'article', 'report', 'update', 'breaking', 'latest', 'story',
                        'journalist', 'press', 'media', 'publish', 'headline', 'coverage',
                        'announced', 'revealed', 'reported', 'according', 'sources']
        
        entertainment_keywords = ['entertainment', 'movie', 'film', 'music', 'game', 'gaming',
                                'video', 'stream', 'streaming', 'watch', 'play', 'listen',
                                'show', 'series', 'episode', 'artist', 'album', 'song']
        
        social_keywords = ['social', 'friend', 'follow', 'share', 'post', 'comment', 'like',
                          'message', 'chat', 'connect', 'community', 'profile', 'feed',
                          'timeline', 'status', 'update', 'notification']
        
        health_keywords = ['health', 'medical', 'doctor', 'patient', 'hospital', 'clinic',
                          'disease', 'treatment', 'medicine', 'wellness', 'fitness', 'care',
                          'symptoms', 'diagnosis', 'therapy', 'healthy']
        
        finance_keywords = ['bank', 'banking', 'financial', 'money', 'loan', 'credit', 'debit',
                           'account', 'transaction', 'payment', 'insurance', 'investment',
                           'trading', 'stock', 'fund', 'interest', 'mortgage', 'savings']
        
        travel_keywords = ['travel', 'hotel', 'flight', 'booking', 'vacation', 'trip',
                          'destination', 'tour', 'airport', 'ticket', 'resort', 'tourist',
                          'accommodation', 'reservation', 'journey']
        
        # Calculate keyword scores with normalization
        text_lower = text.lower()
        tech_score = sum(1 for word in tech_keywords if word in text_lower) / max(word_count, 1) * 100
        business_score = sum(1 for word in business_keywords if word in text_lower) / max(word_count, 1) * 100
        ecommerce_score = sum(1 for word in ecommerce_keywords if word in text_lower) / max(word_count, 1) * 100
        education_score = sum(1 for word in education_keywords if word in text_lower) / max(word_count, 1) * 100
        news_score = sum(1 for word in news_keywords if word in text_lower) / max(word_count, 1) * 100
        entertainment_score = sum(1 for word in entertainment_keywords if word in text_lower) / max(word_count, 1) * 100
        social_score = sum(1 for word in social_keywords if word in text_lower) / max(word_count, 1) * 100
        health_score = sum(1 for word in health_keywords if word in text_lower) / max(word_count, 1) * 100
        finance_score = sum(1 for word in finance_keywords if word in text_lower) / max(word_count, 1) * 100
        travel_score = sum(1 for word in travel_keywords if word in text_lower) / max(word_count, 1) * 100
        
        # Action words (verbs that indicate website purpose)
        action_words = ['buy', 'sell', 'learn', 'read', 'watch', 'play', 'download', 
                       'subscribe', 'register', 'login', 'search', 'browse', 'shop']
        action_score = sum(1 for word in action_words if word in text_lower) / max(word_count, 1) * 100
        
        # Call-to-action indicators
        cta_words = ['free', 'now', 'today', 'join', 'get', 'start', 'try', 'click']
        cta_score = sum(1 for word in cta_words if word in text_lower) / max(word_count, 1) * 100
        
        features.append({
            'word_count': word_count,
            'char_count': char_count,
            'avg_word_length': avg_word_length,
            'unique_ratio': unique_ratio,
            'avg_sentence_length': avg_sentence_length,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'comma_count': comma_count,
            'tech_score': tech_score,
            'business_score': business_score,
            'ecommerce_score': ecommerce_score,
            'education_score': education_score,
            'news_score': news_score,
            'entertainment_score': entertainment_score,
            'social_score': social_score,
            'health_score': health_score,
            'finance_score': finance_score,
            'travel_score': travel_score,
            'action_score': action_score,
            'cta_score': cta_score
        })
    
    return pd.DataFrame(features)

# Load and preprocess data
print("🚀 Training ENHANCED website category model...")
cat_df = pd.read_csv("website_classification.csv")

text_col = "cleaned_website_text"
cat_df = cat_df.dropna(subset=[text_col, "Category"]).reset_index(drop=True)

print(f"📊 Original dataset: {len(cat_df)} samples")

# Apply enhanced preprocessing
print("🔧 Applying enhanced text preprocessing...")
cat_df[text_col] = cat_df[text_col].apply(advanced_text_preprocessing)

# Remove very short text (need meaningful content)
cat_df = cat_df[cat_df[text_col].str.len() >= 100].reset_index(drop=True)

# Remove categories with too few samples (need at least 15 for better training)
category_counts = cat_df["Category"].value_counts()
print(f"\n📊 Category distribution before filtering:")
print(category_counts)

valid_categories = category_counts[category_counts >= 15].index
cat_df = cat_df[cat_df["Category"].isin(valid_categories)].reset_index(drop=True)

print(f"\n✅ Filtered dataset: {len(cat_df)} samples, {len(valid_categories)} categories")
print(f"📊 Category distribution:")
print(cat_df["Category"].value_counts())

# Create enhanced features
print("\n🔧 Creating enhanced features...")
enhanced_features = create_enhanced_features(cat_df, text_col)

# Encode labels
label_encoder = LabelEncoder()
y_cat = label_encoder.fit_transform(cat_df["Category"])

# Enhanced TF-IDF with optimized parameters for faster training
print("🔧 Creating TF-IDF features...")
tfidf = TfidfVectorizer(
    max_features=8000,  # Reduced from 15000 for faster training
    ngram_range=(1, 2),  # Reduced from (1, 3) to bigrams only
    min_df=2,  # Reduced from 3 for more features
    max_df=0.9,  # Increased from 0.85 to keep more terms
    stop_words='english',
    sublinear_tf=True,  # Use sublinear term frequency scaling
    norm='l2'
)

# Transform text
X_text = tfidf.fit_transform(cat_df[text_col])

# Combine text and enhanced features
X_combined = np.hstack([X_text.toarray(), enhanced_features.values])

print(f"📊 Total features: {X_combined.shape[1]}")

# Feature selection to reduce overfitting
print("🔧 Selecting best features...")
k_features = min(3000, X_combined.shape[1])  # Reduced from 5000 for faster training
selector = SelectKBest(chi2, k=k_features)
X_selected = selector.fit_transform(X_combined, y_cat)

print(f"📊 Selected features: {X_selected.shape[1]}")

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_selected)

# Split data with stratification
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_cat, test_size=0.2, random_state=42, stratify=y_cat
)

print(f"\n📊 Training set: {X_train.shape[0]} samples")
print(f"📊 Test set: {X_test.shape[0]} samples")

# Create single Random Forest model (faster and more reliable)
print("\n🎯 Training Random Forest model...")

# Single Random Forest with optimized parameters
ensemble_model = RandomForestClassifier(
    n_estimators=100,  # Good balance of speed and performance
    max_depth=15,      # Reasonable depth
    min_samples_split=5,
    min_samples_leaf=2,
    max_features='sqrt',
    random_state=42,
    n_jobs=1,  # Single thread to avoid conflicts
    class_weight='balanced'
)

# Train model with progress tracking
print("Training Random Forest (this may take a few minutes)...")
print("🔄 Training model...")
ensemble_model.fit(X_train, y_train)
print("✅ Model training complete!")

# Evaluate
y_pred = ensemble_model.predict(X_test)
y_pred_proba = ensemble_model.predict_proba(X_test)

final_accuracy = metrics.accuracy_score(y_test, y_pred)
final_f1 = metrics.f1_score(y_test, y_pred, average='weighted')
final_precision = metrics.precision_score(y_test, y_pred, average='weighted')
final_recall = metrics.recall_score(y_test, y_pred, average='weighted')

print(f"\n🎉 FINAL ENSEMBLE MODEL PERFORMANCE:")
print(f"Accuracy:  {final_accuracy:.3f}")
print(f"F1 Score:  {final_f1:.3f}")
print(f"Precision: {final_precision:.3f}")
print(f"Recall:    {final_recall:.3f}")

if final_accuracy >= 0.90:
    print("🏆 OUTSTANDING! 90%+ accuracy achieved!")
elif final_accuracy >= 0.85:
    print("🎯 EXCELLENT! 85%+ accuracy achieved!")
elif final_accuracy >= 0.75:
    print("🔥 Good performance! 75%+ accuracy achieved.")
else:
    print("📈 Decent performance, can be improved with more data.")

# Detailed classification report
print("\n📊 Per-category performance:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_, zero_division=0))

# Calculate per-category confidence
print("\n📊 Average confidence per category:")
for i, category in enumerate(label_encoder.classes_):
    mask = y_test == i
    if mask.sum() > 0:
        avg_confidence = y_pred_proba[mask, i].mean() * 100
        print(f"{category}: {avg_confidence:.2f}%")

# Save the enhanced model
os.makedirs("pickle", exist_ok=True)

model_data = {
    'ensemble_model': ensemble_model,
    'tfidf_vectorizer': tfidf,
    'label_encoder': label_encoder,
    'feature_columns': enhanced_features.columns.tolist(),
    'feature_selector': selector,
    'scaler': scaler,
    'accuracy': final_accuracy,
    'f1_score': final_f1
}

with open("pickle/category_model_advanced.pkl", "wb") as f:
    pickle.dump(model_data, f)

print("\n💾 Saved enhanced category model as category_model_advanced.pkl")
print("✅ Model training complete!")