
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

# Configuration selected using validation data
THRESHOLD = 0.45
TARGET = "default_next_month"

features = [
    "limit_bal",
    "pay_status_sep",
    "pay_status_aug",
    "pay_status_jul",
    "pay_status_jun",
    "pay_status_may",
    "pay_status_apr",
    "bill_amt1",
    "bill_amt2",
    "bill_amt3",
    "bill_amt4",
    "bill_amt5",
    "bill_amt6",
    "pay_amt1",
    "pay_amt2",
    "pay_amt3",
    "pay_amt4",
    "pay_amt5",
    "pay_amt6",
]

# Load data and remove exact duplicate rows
df = pd.read_csv("cleaned_credit_risk.csv").drop_duplicates()

X = df[features]
y = df[TARGET]

# Reserve test data before model training
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

# Use the same preprocessing as the previous experiments
preprocessor = ColumnTransformer([
    (
        "numeric",
        Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]),
        features,
    )
])

# Retrain on the full 80% development set
model = Pipeline([
    ("preprocessing", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    )),
])

model.fit(X_trainval, y_trainval)

# Evaluate once on the untouched test set
probabilities = model.predict_proba(X_test)[:, 1]
predictions = (probabilities >= THRESHOLD).astype(int)

print("\nFINAL TEST RESULTS")
print("Threshold:", THRESHOLD)
print("Test rows:", len(y_test))
print("Accuracy:", round(accuracy_score(y_test, predictions), 4))
print("Precision:", round(
    precision_score(y_test, predictions, zero_division=0), 4
))
print("Recall:", round(
    recall_score(y_test, predictions, zero_division=0), 4
))
print("F1-score:", round(
    f1_score(y_test, predictions, zero_division=0), 4
))
print("ROC-AUC:", round(
    roc_auc_score(y_test, probabilities), 4
))

print("\nConfusion matrix [[TN, FP], [FN, TP]]:")
print(confusion_matrix(y_test, predictions))

print("\nClassification report:")
print(classification_report(
    y_test, predictions, zero_division=0
))

print("\nExample risk scores:")
for probability in probabilities[:5]:
    risk_score = round(probability * 100)
    print(
        f"Default probability: {probability:.1%} | "
        f"Prototype risk score: {risk_score}/100"
    )
