# predict.py
import joblib
from sklearn.datasets import load_breast_cancer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

# Load trained global model
model = joblib.load("global_model.pkl")

# Load dataset
X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Predict on test data
preds = model.predict(X_test)
acc = accuracy_score(y_test, preds)

print("✅ Global Model Test Accuracy:", acc)

# Show some predictions vs actual
print("Predictions:", preds[:10])
print("Actual     :", y_test[:10])
