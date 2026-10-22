
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "cleaned_credit_risk.csv"
MODEL_PATH = Path(__file__).resolve().parent / "credit_risk_model.joblib"

TARGET = "default_next_month"
THRESHOLD = 0.45
MODEL_VERSION = "1.0"

FEATURES = [
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


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH).drop_duplicates()

    required_columns = FEATURES + [TARGET]
    missing = set(required_columns) - set(df.columns)

    if missing:
        raise ValueError(
            f"Dataset is missing columns: {sorted(missing)}"
        )

    X = df[FEATURES]
    y = df[TARGET]

    preprocessor = ColumnTransformer([
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]),
            FEATURES,
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

    print(f"Training on {len(df)} rows...")
    model.fit(X, y)

    artifact = {
        "model": model,
        "features": FEATURES,
        "threshold": THRESHOLD,
        "model_name": "Random Forest",
        "model_version": MODEL_VERSION,
        "training_rows": len(df),
    }

    joblib.dump(artifact, MODEL_PATH)

    # Verify that the saved artifact can be loaded.
    loaded = joblib.load(MODEL_PATH)
    probabilities = loaded["model"].predict_proba(
        X.iloc[:3]
    )[:, 1]

    print(f"Saved model to: {MODEL_PATH}")
    print(f"Model version: {MODEL_VERSION}")
    print(f"Training rows: {len(df)}")
    print("Test probabilities:", probabilities.round(4))


if __name__ == "__main__":
    main()
