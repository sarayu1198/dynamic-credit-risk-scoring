"""
Prepare the cleaned UCI Default of Credit Card Clients dataset.

Run:
    pip install pandas scikit-learn
    python prepare_credit_risk.py

The script performs a stratified 80/20 split and shows safe preprocessing
pipelines. Imputation/scaling are fit only on training folds by scikit-learn.
"""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)

DATA_PATH = Path("cleaned_credit_risk.csv")
TARGET = "default_next_month"
RANDOM_STATE = 42

df = pd.read_csv(DATA_PATH)
if TARGET not in df.columns:
    raise ValueError(f"Missing target column: {TARGET}")

# Initial feature set: financial and repayment behaviour only.
# Demographic/profile fields are intentionally excluded for this first experiment.
excluded = [c for c in ["sex", "education", "marriage", "age"] if c in df.columns]
X = df.drop(columns=[TARGET] + excluded)
y = df[TARGET].astype(int)

print("Dataset shape:", df.shape)
print("Duplicate rows:", int(df.duplicated().sum()))
print("Missing values by column:")
print(df.isna().sum()[df.isna().sum() > 0])
print("\nTarget distribution:")
print(y.value_counts().sort_index())
print((y.value_counts(normalize=True).sort_index() * 100).round(2).astype(str) + "%")
print("\nFeatures used:", list(X.columns))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
)
print(f"\nTrain rows: {len(X_train):,}; test rows: {len(X_test):,}")
print("Train target proportions:")
print(y_train.value_counts(normalize=True).sort_index().round(4))
print("Test target proportions:")
print(y_test.value_counts(normalize=True).sort_index().round(4))

# Numeric features only in this initial feature set. Median imputation and scaling
# are inside the pipeline, preventing preprocessing leakage from the test set.
numeric_preprocessing = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

preprocessor = ColumnTransformer(
    transformers=[("numeric", numeric_preprocessing, list(X.columns))],
    remainder="drop"
)

models = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE,
        n_jobs=-1, min_samples_leaf=2
    ),
}

# Optional XGBoost. Install with: pip install xgboost
try:
    from xgboost import XGBClassifier
    models["XGBoost"] = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9,
        eval_metric="logloss", random_state=RANDOM_STATE
    )
except ImportError:
    print("\nXGBoost not installed; skipping it. Install with: pip install xgboost")

# This is a starter comparison, not hyperparameter tuning.
# For final reporting, tune on training data using stratified cross-validation.
results = []
for name, model in models.items():
    pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    proba = pipe.predict_proba(X_test)[:, 1]
    row = {
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, proba),
    }
    results.append(row)
    print(f"\n--- {name} ---")
    print({k: round(v, 4) if isinstance(v, float) else v for k, v in row.items()})
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    print(confusion_matrix(y_test, pred))
    print(classification_report(y_test, pred, zero_division=0))

print("\nModel comparison:")
print(pd.DataFrame(results).sort_values("roc_auc", ascending=False).to_string(index=False))
