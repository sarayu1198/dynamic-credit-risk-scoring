
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
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

# 1. Load data and remove exact duplicate rows
df = pd.read_csv("cleaned_credit_risk.csv")

print("Original dataset shape:", df.shape)

duplicate_count = int(df.duplicated().sum())
df = df.drop_duplicates().reset_index(drop=True)

print("Exact duplicate rows removed:", duplicate_count)
print("Cleaned dataset shape:", df.shape)

target = "default_next_month"

# 2. Use the same financial/repayment features as before
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

X = df[features]
y = df[target]

print("\nTarget distribution:")
print(y.value_counts())
print((y.value_counts(normalize=True) * 100).round(2))

# 3. Create a stratified 80/20 train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print("\nTrain rows:", len(X_train))
print("Test rows:", len(X_test))

# 4. Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]),
            features,
        )
    ]
)

# 5. Define models
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    ),
}

# XGBoost is optional if its library is unavailable
try:
    from xgboost import XGBClassifier

    models["XGBoost"] = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
except (ImportError, OSError) as error:
    print("\nXGBoost could not be imported:", error)

# 6. Train and evaluate each model
results = []

for name, model in models.items():
    pipeline = Pipeline([
        ("preprocessing", preprocessor),
        ("model", model),
    ])

    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(
            y_test, predictions, zero_division=0
        ),
        "recall": recall_score(
            y_test, predictions, zero_division=0
        ),
        "f1": f1_score(
            y_test, predictions, zero_division=0
        ),
        "roc_auc": roc_auc_score(y_test, probabilities),
    }
    results.append(metrics)

    print(f"\n--- {name} ---")
    print({
        key: round(value, 4) if isinstance(value, float) else value
        for key, value in metrics.items()
    })
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    print(confusion_matrix(y_test, predictions))
    print(classification_report(
        y_test,
        predictions,
        zero_division=0,
    ))

# 7. Final comparison
comparison = pd.DataFrame(results)
comparison = comparison.sort_values("roc_auc", ascending=False)

print("\nMODEL COMPARISON")
print(comparison.round(4).to_string(index=False))

comparison.to_csv("credit_risk_model_comparison_v2.csv", index=False)
print("\nSaved comparison to credit_risk_model_comparison_v2.csv")

