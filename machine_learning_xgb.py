# ─────────────────────────────────────────────────────────────────────────────
# XGBoost Phishing Detector — Maximum Accuracy Edition
#
# Why XGBoost beats Random Forest for phishing detection:
#  - Handles imbalanced data better with scale_pos_weight
#  - Built-in regularization prevents overfitting
#  - Gradient boosting learns from mistakes each round
#  - Typically 1-3% more accurate than RF on structured/tabular data
# ─────────────────────────────────────────────────────────────────────────────

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import (
    confusion_matrix, f1_score, accuracy_score,
    precision_score, recall_score, classification_report
)


# ── Step 1  Load & prepare data ───────────────────────────────────────────────
legitimate_df = pd.read_csv(Path("datasets") / "structured_data_legitimate.csv")
phishing_df   = pd.read_csv(Path("datasets") / "structured_data_phishing.csv")

df = (
    pd.concat([
        pd.DataFrame(legitimate_df).drop_duplicates(),
        pd.DataFrame(phishing_df).drop_duplicates()
    ], axis=0)
    .drop_duplicates()
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)

if "URL" in df.columns:
    df = df.drop("URL", axis=1)

X = df.drop(columns=["label"])
Y = df["label"]

# Class balance check — XGBoost handles this automatically
n_legit  = (Y == 0).sum()
n_phish  = (Y == 1).sum()
scale_pw = round(n_legit / n_phish, 2)   # weight to balance classes

print(f"Dataset     : {len(df)} rows")
print(f"Features    : {X.shape[1]}")
print(f"Legitimate  : {n_legit}")
print(f"Phishing    : {n_phish}")
print(f"Class weight: {scale_pw}  (auto-balancing)\n")


# ── Step 2  XGBoost with best parameters for maximum accuracy ─────────────────
# These parameters are tuned specifically for phishing detection:
#   n_estimators     — more trees = better accuracy (diminishing returns > 500)
#   max_depth        — deeper trees catch complex phishing patterns
#   learning_rate    — lower = more careful learning (needs more trees)
#   subsample        — prevents overfitting by using 80% of data per tree
#   colsample_bytree — prevents overfitting by using 80% of features per tree
#   scale_pos_weight — balances phishing vs legitimate class sizes
#   eval_metric      — optimise for log loss (best for probability output)

xgb_model = XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pw,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1        # use all CPU cores for speed
)


# ── Step 3  Stratified K-Fold (better than plain K-Fold) ─────────────────────
# StratifiedKFold keeps the same phishing/legitimate ratio in every fold,
# giving more reliable accuracy scores than plain K-Fold.

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

accuracy_list, precision_list, recall_list, f1_list = [], [], [], []

print("Running 5-Fold Cross Validation...")
for fold, (train_idx, test_idx) in enumerate(skf.split(X, Y), 1):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    Y_train, Y_test = Y.iloc[train_idx], Y.iloc[test_idx]

    xgb_model.fit(
        X_train, Y_train,
        eval_set=[(X_test, Y_test)],
        verbose=False
    )

    preds = xgb_model.predict(X_test)
    tn, fp, fn, tp = confusion_matrix(Y_test, preds).ravel()

    acc  = accuracy_score(Y_test, preds)
    prec = precision_score(Y_test, preds)
    rec  = recall_score(Y_test, preds)
    f1   = f1_score(Y_test, preds)

    accuracy_list.append(acc)
    precision_list.append(prec)
    recall_list.append(rec)
    f1_list.append(f1)

    print(f"  Fold {fold}: Accuracy={acc:.4f}  Precision={prec:.4f}  "
          f"Recall={rec:.4f}  F1={f1:.4f}")


# ── Step 4  Print benchmark results ──────────────────────────────────────────
def avg(lst): return round(sum(lst) / len(lst), 6)

print("\n=== XGBoost Cross-Validation Results ===")
print(f"  Accuracy  : {avg(accuracy_list)}")
print(f"  Precision : {avg(precision_list)}")
print(f"  Recall    : {avg(recall_list)}")
print(f"  F1 Score  : {avg(f1_list)}")


# ── Step 5  Final train on FULL dataset then save ─────────────────────────────
print("\nRe-training XGBoost on full dataset for maximum accuracy...")

xgb_model.fit(X, Y, verbose=False)

# Show top 10 most important features
feat_importance = pd.Series(
    xgb_model.feature_importances_, index=X.columns
).sort_values(ascending=False)

print("\nTop 10 Most Important Features:")
print(feat_importance.head(10).to_string())

# Save the model
MODELS_DIR = Path("trained_models")
MODELS_DIR.mkdir(exist_ok=True)

with open(MODELS_DIR / "xgb_model_saved", "wb") as f:
    pickle.dump(xgb_model, f)

print("\nSaved: trained_models/xgb_model_saved")
print("XGBoost model ready. Now update ml_app_screen.py and machine_learning.py.")