
import pandas as pd

# Load the cleaned dataset
df = pd.read_csv("cleaned_credit_risk.csv")

target = "default_next_month"
features = [col for col in df.columns if col != target]

# 1. Exact duplicate rows: same features AND same target
exact_duplicates = df.duplicated(keep="first")
print("Total rows:", len(df))
print("Exact duplicate rows beyond first occurrence:", exact_duplicates.sum())

# 2. Duplicate feature combinations, regardless of target
duplicate_features = df.duplicated(subset=features, keep=False)
print(
    "Rows sharing a feature combination:",
    duplicate_features.sum()
)

# 3. Check whether identical features have conflicting target labels
label_counts = df.groupby(features, dropna=False)[target].nunique()
conflicting_groups = label_counts[label_counts > 1]

print(
    "Feature combinations with conflicting target labels:",
    len(conflicting_groups)
)

# Show examples of conflicting labels, if any
if len(conflicting_groups) > 0:
    examples = (
        df.set_index(features)
        .loc[conflicting_groups.index]
        .reset_index()
    )
    print("\nExamples of conflicting labels:")
    print(examples.head(10).to_string(index=False))

# 4. Show examples of exact duplicate rows
if exact_duplicates.sum() > 0:
    print("\nExamples of exact duplicate rows:")
    print(df.loc[exact_duplicates].head(10).to_string(index=False))
