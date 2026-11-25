"""Train, evaluate, and plot the TrackFlow monthly sales forecast.

Random Forest is used because the documented dataset has only 120 monthly
observations, can contain nonlinear seasonal effects, and needs a quick,
reasonably explainable model rather than an expensive hyperparameter search.
Although tree splits are scale-invariant, a StandardScaler is included in the
pipeline so the preprocessing contract remains explicit and can be extended
without changing the estimator.

The test period is never used to fit the imputation, model, or any other
learned preprocessing step.  Missing and whitespace-only values are treated
as nulls and incomplete rows are removed before the temporal split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    "month",
    "revenue_eur",
    "shipments_processed",
    "avg_revenue_per_shipment_eur",
    "market",
)
TARGET: Final[str] = "revenue_eur"
YEARS_FOR_TRAINING: Final[int] = 8
YEARS_FOR_TESTING: Final[int] = 2


def load_and_clean(path: Path) -> pd.DataFrame:
    """Load the documented schema and remove unusable rows."""
    frame = pd.read_csv(path, na_values=["", " ", "NA", "N/A", "null", "None"])
    frame.columns = frame.columns.str.strip()
    if tuple(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns. Expected {EXPECTED_COLUMNS}, "
            f"received {tuple(frame.columns)}"
        )

    for column in frame.select_dtypes(include=["object"]).columns:
        frame[column] = frame[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    frame["month"] = pd.to_datetime(frame["month"], errors="coerce")
    for column in ("revenue_eur", "shipments_processed", "avg_revenue_per_shipment_eur"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.loc[frame["market"].eq("consolidated")].copy()
    frame = frame.dropna(subset=EXPECTED_COLUMNS).sort_values("month")
    if frame.empty:
        raise ValueError("No complete consolidated rows remain after cleaning.")
    if frame["month"].duplicated().any():
        raise ValueError("Duplicate consolidated months remain after cleaning.")
    if (frame[TARGET] <= 0).any():
        raise ValueError("revenue_eur must be positive.")
    return frame.reset_index(drop=True)


def make_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build causal calendar, lag, and rolling features."""
    features = pd.DataFrame(index=frame.index)
    month_number = frame["month"].dt.month
    features["month_sin"] = np.sin(2 * np.pi * month_number / 12)
    features["month_cos"] = np.cos(2 * np.pi * month_number / 12)
    features["trend_month"] = np.arange(len(frame))
    for lag in (1, 3, 6, 12):
        features[f"revenue_lag_{lag}"] = frame[TARGET].shift(lag)
    shifted_target = frame[TARGET].shift(1)
    for window in (3, 6, 12):
        features[f"revenue_rolling_mean_{window}"] = shifted_target.rolling(window).mean()
    features["shipments_processed"] = frame["shipments_processed"]
    features["avg_revenue_per_shipment_eur"] = frame["avg_revenue_per_shipment_eur"]
    return features, frame[TARGET].copy()


def split_temporally(
    frame: pd.DataFrame, features: pd.DataFrame, target: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Return the first eight years for training and the last two for testing."""
    first_year = int(frame["month"].dt.year.min())
    last_year = int(frame["month"].dt.year.max())
    expected_last_year = first_year + YEARS_FOR_TRAINING + YEARS_FOR_TESTING - 1
    if last_year != expected_last_year:
        raise ValueError(
            "Expected ten consecutive calendar years, from "
            f"{first_year} to {expected_last_year}; received through {last_year}."
        )
    train_end = pd.Timestamp(year=first_year + YEARS_FOR_TRAINING, month=1, day=1)
    train_mask = frame["month"] < train_end
    test_mask = frame["month"] >= train_end
    usable = features.notna().all(axis=1)
    train_mask &= usable
    test_mask &= usable
    if train_mask.sum() != 84 or test_mask.sum() != 24:
        raise ValueError(
            "Expected 84 usable training rows and 24 test rows after causal "
            f"features; received {train_mask.sum()} and {test_mask.sum()}."
        )
    return (
        features.loc[train_mask],
        features.loc[test_mask],
        target.loc[train_mask],
        target.loc[test_mask],
    )


def _population_stability_index(reference: pd.Series, current: pd.Series) -> float:
    """Calculate PSI using reference quantiles and stable epsilon bins."""
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, 11)))
    if len(edges) < 2:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    reference_rate = np.maximum(np.histogram(reference, edges)[0] / len(reference), 1e-6)
    current_rate = np.maximum(np.histogram(current, edges)[0] / len(current), 1e-6)
    return float(np.sum((current_rate - reference_rate) * np.log(current_rate / reference_rate)))


def _normalized_gini(actual: pd.Series, predicted: np.ndarray) -> float:
    """Calculate normalized cumulative-gain Gini for a regression forecast."""
    actual_values = np.asarray(actual, dtype=float)
    if np.all(actual_values == actual_values[0]):
        return 0.0

    def gini(values: np.ndarray, scores: np.ndarray) -> float:
        order = np.argsort(-scores, kind="stable")
        cumulative = np.cumsum(values[order])
        return float(np.sum(cumulative) / cumulative[-1] - (len(values) + 1) / 2)

    baseline = gini(actual_values, actual_values)
    return 0.0 if baseline == 0 else gini(actual_values, predicted) / baseline


def calculate_metrics(
    y_train: pd.Series, y_test: pd.Series, predictions: np.ndarray
) -> dict[str, float]:
    """Return MSE, PSI, normalized Gini, and the defined K2 (R²) score.

    K2 is reported as the coefficient of determination (R²), the convention
    used by this implementation for the requested regression K2 metric.
    """
    return {
        "mse_eur_squared": float(mean_squared_error(y_test, predictions)),
        "psi": _population_stability_index(y_train, y_test),
        "gini": float(_normalized_gini(y_test, predictions)),
        "k2_score": float(r2_score(y_test, predictions)),
    }


def plot_forecast(
    frame: pd.DataFrame,
    y_test: pd.Series,
    predictions: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    output_path: Path,
) -> None:
    """Save test observations, forecast, and tree-derived variability band."""
    test_months = frame.loc[y_test.index, "month"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(11, 5))
    axis.plot(test_months, y_test, label="Real", color="#1f2937", marker="o")
    axis.plot(test_months, predictions, label="Predicción", color="#2563eb")
    axis.fill_between(
        test_months,
        lower,
        upper,
        color="#93c5fd",
        alpha=0.35,
        label="Variabilidad (P10-P90)",
    )
    axis.set(
        title="TrackFlow: ventas reales frente a predicción (2 años de prueba)",
        xlabel="Mes",
        ylabel="Ingresos (EUR)",
    )
    axis.legend()
    axis.grid(alpha=0.2)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def train_and_evaluate(
    path: Path,
    plot_path: Path = Path("data/process/trackflow_sales_forecast.png"),
) -> dict[str, object]:
    """Train on the first eight years and evaluate on the latest two."""
    frame = load_and_clean(path)
    features, target = make_features(frame)
    x_train, x_test, y_train, y_test = split_temporally(frame, features, target)
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                    min_samples_leaf=2,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    forest = model.named_steps["regressor"]
    tree_predictions = np.vstack(
        [tree.predict(model.named_steps["scaler"].transform(x_test)) for tree in forest.estimators_]
    )
    lower, upper = np.percentile(tree_predictions, [10, 90], axis=0)
    plot_forecast(frame, y_test, predictions, lower, upper, plot_path)
    return {
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "test_start": frame.loc[y_test.index, "month"].min().date().isoformat(),
        "test_end": frame.loc[y_test.index, "month"].max().date().isoformat(),
        "plot_path": str(plot_path),
        "metrics": calculate_metrics(y_train, y_test, predictions),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset",
        nargs="?",
        type=Path,
        default=Path("data/raw/trackflow_sales.csv"),
    )
    parser.add_argument(
        "--plot",
        type=Path,
        default=Path("data/process/trackflow_sales_forecast.png"),
        help="Path for the real-vs-predicted forecast plot.",
    )
    args = parser.parse_args()
    print(json.dumps(train_and_evaluate(args.dataset, args.plot), indent=2))


if __name__ == "__main__":
    main()
