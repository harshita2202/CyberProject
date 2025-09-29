import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import seaborn as sns
import matplotlib.pyplot as plt
import joblib  

df = pd.read_csv("Phishing_Legitimate_full.csv")

df = df.drop(columns=["id"])

df = df.sample(frac=1, random_state=42).reset_index(drop=True)

X = df.drop(columns=["CLASS_LABEL"])
y = df["CLASS_LABEL"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = xgb.XGBClassifier(eval_metric="logloss", random_state=42)

print("\nTraining XGBoost...")
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
print(f"\nXGBoost Accuracy: {acc:.4f}")
print("\nClassification Report:\n", classification_report(y_test, y_pred))

cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("XGBoost Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.show()

joblib.dump(model, "xgboost_model.pkl")
print("\nModel saved as xgboost_model.pkl")