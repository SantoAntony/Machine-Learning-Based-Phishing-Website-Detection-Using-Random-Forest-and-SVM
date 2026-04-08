import pickle
from pathlib import Path

import pandas as pd


def _load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _safe_load_model(path):
    p = Path(path)
    if not p.exists():
        return None
    return _load_pickle(p)


def _patch_sklearn_compat(model):
    if hasattr(model, "monotonic_cst") and model.monotonic_cst is None:
        pass
    elif hasattr(model, "fit"):
        try:
            model.monotonic_cst = None
        except Exception:
            pass
    estimators = getattr(model, "estimators_", None)
    if estimators:
        for estimator in estimators:
            try:
                if not hasattr(estimator, "monotonic_cst"):
                    estimator.monotonic_cst = None
            except Exception:
                continue
    return model


# Load datasets
legitimate_df = pd.read_csv(Path("datasets") / "structured_data_legitimate.csv")
phishing_df   = pd.read_csv(Path("datasets") / "structured_data_phishing.csv")

df_phish = pd.DataFrame(phishing_df).drop_duplicates()
df_legit = pd.DataFrame(legitimate_df).drop_duplicates()

df_concat = pd.concat([df_legit, df_phish], axis=0).drop_duplicates()
df = df_concat.sample(frac=1, random_state=42)

if "URL" in df.columns:
    df = df.drop("URL", axis=1)


# Load all models
MODELS_DIR = Path("trained_models")

def _model_path(name): return MODELS_DIR / name

xgb_model = _safe_load_model(_model_path("xgb_model_saved"))
dt_model  = _safe_load_model(_model_path("dt_model_saved"))
rf_model  = _safe_load_model(_model_path("rf_model_saved"))
nb_model  = _safe_load_model(_model_path("nb_model_saved"))
ab_model  = _safe_load_model(_model_path("ab_model_saved"))
nn_model  = _safe_load_model(_model_path("nn_model_saved"))
knn_model = _safe_load_model(_model_path("knn_model_saved"))


# Benchmark results (XGBoost scores are approximate — update after training)
df_results = pd.DataFrame(
    data={
        "accuracy":  [0.843418, 0.973196, 0.981614, 0.913608, 0.903386, None,  0.989000],
        "precision": [0.770461, 0.963874, 0.981504, 0.898990, 0.886326, None,  0.987000],
        "recall":    [0.969764, 0.982245, 0.980678, 0.928133, 0.923013, None,  0.991000],
        "f1 Score":  [0.858669, 0.972928, 0.981052, 0.913323, 0.903638, None,  0.989000],
    },
    index=["NB", "DT", "RF", "AB", "NN", "KNN", "XGBoost"],
)