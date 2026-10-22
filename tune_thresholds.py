
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
)

# Load data and remove exact duplicates
df = pd.read_csv("cleaned_credit_risk.csv").drop_duplicates()

target = "default_next_month"

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

# First reserve 20% as a final test set
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

# Split remaining data into training and validation
X_train, X_val, y_train, y_val = train_test_split(
    X_trainval, y_trainval,
    test_size=0.20,
    random_state=42,
    stratify=y_trainval,
)

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

model.fit(X_train, y_train)

# Probabilities for the positive class: default = 1
val_probabilities = model.predict_proba(X_val)[:, 1]

results = []

for threshold in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
    val_predictions = (val_probabilities >= threshold).astype(int)

    results.append({
        "threshold": threshold,
        "accuracy": accuracy_score(y_val, val_predictions),
        "precision": precision_score(
            y_val, val_predictions, zero_division=0
        ),
        "recall": recall_score(
            y_val, val_predictions, zero_division=0
        ),
        "f1": f1_score(
            y_val, val_predictions, zero_division=0
        ),
    })

results_df = pd.DataFrame(results)

print("\nVALIDATION RESULTS BY THRESHOLD")
print(results_df.round(4).to_string(index=False))

print("\nBest threshold by validation F1:")
print(
    results_df.loc[results_df["f1"].idxmax()]
    .round(4)
    .to_string()
)

print("\nValidation ROC-AUC:", round(
    roc_auc_score(y_val, val_probabilities), 4
))

results_df.to_csv("threshold_tuning_results.csv", index=False)
print("\nSaved results to threshold_tuning_results.csv")
