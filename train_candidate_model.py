
from pathlib import Path
import json

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline


# Project paths
ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "cleaned_credit_risk.csv"
OUTPUT_DIR = ROOT / "model_experiments"
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET = "default_next_month"
RANDOM_STATE = 42


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    data = pd.read_csv(DATA_PATH)

    if TARGET not in data.columns:
        raise ValueError(f"Missing target column: {TARGET}")

    # Remove only rows that are exact duplicates across all columns.
    original_rows = len(data)
    data = data.drop_duplicates().copy()
    exact_duplicates_removed = original_rows - len(data)

    X = data.drop(columns=[TARGET])
    y = data[TARGET].astype(int)

    # Keep identical feature combinations in the same split.
    # This prevents identical feature rows from leaking across train/test.
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_STATE,
    )

    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    print("\n=== DATASET ===")
    print(f"Original rows: {original_rows}")
    print(f"Exact duplicate rows removed: {exact_duplicates_removed}")
    print(f"Rows after exact deduplication: {len(data)}")
    print(f"Feature columns: {len(X.columns)}")
    print(f"Training rows: {len(X_train)}")
    print(f"Testing rows: {len(X_test)}")
    print(f"Training default rate: {y_train.mean():.4f}")
    print(f"Testing default rate: {y_test.mean():.4f}")

    # Check whether conflicting labels exist for identical features.
    label_counts = data.groupby(list(X.columns), dropna=False)[TARGET].nunique()
    conflicting_groups = int((label_counts > 1).sum())
    print(f"Feature groups with conflicting labels: {conflicting_groups}")

    # Median imputation is included in the pipeline in case future data has
    # missing values. The original dataset is not modified.
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    print("\nTraining candidate Random Forest...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, probabilities)
    accuracy = accuracy_score(y_test, predictions)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])
    report = classification_report(
        y_test,
        predictions,
        labels=[0, 1],
        target_names=["No default", "Default"],
        zero_division=0,
    )

    print("\n=== CANDIDATE MODEL RESULTS ===")
    print(f"ROC-AUC: {auc:.4f}")
    print(f"Accuracy: {accuracy:.4f}")
    print("\nConfusion matrix (rows = actual, columns = predicted):")
    print(matrix)
    print("\nClassification report:")
    print(report)

    # Save this candidate separately. Never overwrite the current model here.
    model_path = OUTPUT_DIR / "random_forest_candidate.joblib"
    joblib.dump(model, model_path)

    metrics = {
        "model": "RandomForestClassifier",
        "dataset": DATA_PATH.name,
        "original_rows": int(original_rows),
        "rows_after_exact_deduplication": int(len(data)),
        "exact_duplicates_removed": int(exact_duplicates_removed),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "train_default_rate": float(y_train.mean()),
        "test_default_rate": float(y_test.mean()),
        "roc_auc": float(auc),
        "accuracy": float(accuracy),
        "confusion_matrix": matrix.tolist(),
        "scikit_learn_version": sklearn.__version__,
        "joblib_version": joblib.__version__,
        "feature_columns": list(X.columns),
    }

    metrics_path = OUTPUT_DIR / "random_forest_candidate_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))

    print(f"\nCandidate model saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    print("\nYour existing credit_risk_model.joblib was not changed.")


if __name__ == "__main__":
    main()
