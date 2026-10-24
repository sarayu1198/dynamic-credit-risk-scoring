
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "cleaned_credit_risk.csv"
CANDIDATE_PATH = ROOT / "model_experiments" / "random_forest_candidate.joblib"
EXISTING_PATH = ROOT / "backend" / "credit_risk_model.joblib"

TARGET = "default_next_month"
RANDOM_STATE = 42


def evaluate(name, model, X_test, y_test, threshold):
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)

    print(f"\n--- {name} | threshold={threshold:.2f} ---")
    print(f"ROC-AUC:  {roc_auc_score(y_test, probabilities):.4f}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print(f"Precision for defaults: {precision_score(y_test, predictions, zero_division=0):.4f}")
    print(f"Recall for defaults:    {recall_score(y_test, predictions, zero_division=0):.4f}")
    print(f"F1 for defaults:        {f1_score(y_test, predictions, zero_division=0):.4f}")
    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions, labels=[0, 1]))


def main():
    for path in (DATA_PATH, CANDIDATE_PATH, EXISTING_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Missing file: {path}")

    data = pd.read_csv(DATA_PATH).drop_duplicates().copy()
    X = data.drop(columns=[TARGET])
    y = data[TARGET].astype(int)

    # Reproduce the candidate's group-aware train/test split.
    groups = pd.util.hash_pandas_object(X, index=False).to_numpy()
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=RANDOM_STATE,
    )
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    candidate = joblib.load(CANDIDATE_PATH)

    print("Held-out test rows:", len(X_test))
    print("Test default rate:", round(y_test.mean(), 4))

    # Evaluate the newly trained 23-feature candidate.
    evaluate(
        "Candidate Random Forest (23 features)",
        candidate,
        X_test,
        y_test,
        threshold=0.50,
    )
    evaluate(
        "Candidate Random Forest (23 features)",
        candidate,
        X_test,
        y_test,
        threshold=0.45,
    )

    # Train a fresh 19-feature baseline on the same training rows.
    # This is a fairer comparison than evaluating the existing artifact,
    # whose metadata says it was trained on all 29,965 rows.
    old_artifact = joblib.load(EXISTING_PATH)
    old_features = old_artifact["features"]

    missing = [column for column in old_features if column not in X.columns]
    if missing:
        raise ValueError(f"Existing model features missing from dataset: {missing}")

    X_train_old = X_train[old_features]
    X_test_old = X_test[old_features]

    baseline = Pipeline(
        steps=[
            (
                "preprocessing",
                ColumnTransformer(
                    transformers=[
                        (
                            "numeric",
                            Pipeline(
                                steps=[
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            old_features,
                        )
                    ]
                ),
            ),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    print("\nTraining fresh 19-feature baseline on training rows only...")
    baseline.fit(X_train_old, y_train)

    evaluate(
        "Fresh baseline (19 features)",
        baseline,
        X_test_old,
        y_test,
        threshold=0.45,
    )

    print(
        "\nNote: the existing saved artifact was not evaluated directly, "
        "because its metadata says it was trained on all 29,965 rows. "
        "Evaluating it on a subset of those rows could give misleading results."
    )


if __name__ == "__main__":
    main()
