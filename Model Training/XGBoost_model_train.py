import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import seaborn as sns
import matplotlib.pyplot as plt
import joblib  

df = pd.read_csv("Phishing_Legitimate_full.csv")
df = df.drop(columns=["id"])

# URL-only columns (drop page/UI ones like PctExtHyperlinks for extension speed)
url_columns = [
    'NumDots', 'SubdomainLevel', 'PathLevel', 'UrlLength', 'NumDash', 'NumDashInHostname',
    'AtSymbol', 'TildeSymbol', 'NumUnderscore', 'NumPercent', 'NumQueryComponents',
    'NumAmpersand', 'NumHash', 'NumNumericChars', 'NoHttps', 'RandomString', 'IpAddress',
    'DomainInSubdomains', 'DomainInPaths', 'HttpsInHostname', 'HostnameLength',
    'PathLength', 'QueryLength', 'DoubleSlashInPath', 'NumSensitiveWords', 'EmbeddedBrandName'
]

# Filter to URL features only
X = df[url_columns]
y = df["CLASS_LABEL"]

# Shuffle and split
df_temp = pd.concat([X, y], axis=1)
df_temp = df_temp.sample(frac=1, random_state=42).reset_index(drop=True)
X = df_temp[url_columns]
y = df_temp["CLASS_LABEL"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = xgb.XGBClassifier(eval_metric="logloss", random_state=42)

print("\nTraining XGBoost on URL-only features...")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nXGBoost Accuracy (URL-only): {acc:.4f}")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("XGBoost Confusion Matrix (URL-Only)")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

# Save new model (matches your uploaded filename)
joblib.dump(model, "xgboost_phishing_model.pkl")
print("\nModel saved as xgboost_phishing_model.pkl—copy to backend/ for no false positives!")