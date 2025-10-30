import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn import metrics
from xgboost import XGBClassifier
import pickle
import os

# 1️⃣ Load dataset
data = pd.read_csv("phishing.csv")

# 2️⃣ Drop unnecessary columns
data = data.drop(['Index'], axis=1)
data['class'] = data['class'].replace(-1, 0)

# 3️⃣ Split features and target
X = data.drop(["class"], axis=1)
y = data["class"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4️⃣ Train model
xgb = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
xgb.fit(X_train, y_train)

# 5️⃣ Evaluate
y_train_pred = xgb.predict(X_train)
y_test_pred = xgb.predict(X_test)

print("\n📊 XGBoost Classifier Performance:")
print("Accuracy (Train): {:.3f}".format(metrics.accuracy_score(y_train, y_train_pred)))
print("Accuracy (Test):  {:.3f}".format(metrics.accuracy_score(y_test, y_test_pred)))
print()

print("F1 Score (Train): {:.3f}".format(metrics.f1_score(y_train, y_train_pred)))
print("F1 Score (Test):  {:.3f}".format(metrics.f1_score(y_test, y_test_pred)))
print()

print("Recall (Train):   {:.3f}".format(metrics.recall_score(y_train, y_train_pred)))
print("Recall (Test):    {:.3f}".format(metrics.recall_score(y_test, y_test_pred)))
print()

print("Precision (Train): {:.3f}".format(metrics.precision_score(y_train, y_train_pred)))
print("Precision (Test):  {:.3f}".format(metrics.precision_score(y_test, y_test_pred)))

# 6️⃣ Save model
os.makedirs("pickle", exist_ok=True)
with open("pickle/model.pkl", "wb") as file:
    pickle.dump(xgb, file)

print("\n💾 Model saved successfully as pickle/model.pkl")