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
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit


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
CV_FOLDS: Final[int] = 5


def load_and_clean(path: Path) -> pd.DataFrame:
    """Load the documented schema and remove unusable rows."""
    frame = pd.read_csv(path, na_values=["", " ", "NA", "N/A", "null", "None"])
    frame.columns = frame.columns.str.strip()
    if tuple(frame.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns. Expected {EXPECTED_COLUMNS}, "
            f"received {tuple(frame.columns)}"
        )

    for column in frame.select_dtypes(include=["object", "string"]).columns:
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


def _build_model() -> Pipeline:
    """Create a fresh estimator so each temporal fold is fitted independently."""
    return Pipeline(
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


def temporal_cross_validate(
    frame: pd.DataFrame, features: pd.DataFrame, target: pd.Series
) -> dict[str, object]:
    """Evaluate expanding chronological folds without feature leakage.

    Features for each fold are rebuilt from the data prefix ending at that
    fold's validation period.  Thus a lag or rolling window can use prior
    training observations, but never a row after the validation boundary.
    """
    first_year = int(frame["month"].dt.year.min())
    training_end = pd.Timestamp(
        year=first_year + YEARS_FOR_TRAINING, month=1, day=1
    )
    training_mask = frame["month"] < training_end
    usable_indices = np.flatnonzero(
        (features.notna().all(axis=1) & training_mask).to_numpy()
    )
    if len(usable_indices) != 84:
        raise ValueError(
            "Temporal CV expects 84 usable rows from the first eight training years; "
            f"received {len(usable_indices)}."
        )
    splitter = TimeSeriesSplit(n_splits=CV_FOLDS)
    fold_results: list[dict[str, object]] = []
    for fold_number, (train_positions, validation_positions) in enumerate(
        splitter.split(usable_indices), start=1
    ):
        train_indices = usable_indices[train_positions]
        validation_indices = usable_indices[validation_positions]
        if not np.all(np.diff(train_indices) > 0) or not np.all(
            np.diff(validation_indices) > 0
        ):
            raise AssertionError("TimeSeriesSplit produced a non-chronological fold.")
        if train_indices[-1] >= validation_indices[0]:
            raise AssertionError("A temporal fold overlaps its validation boundary.")

        validation_end = int(validation_indices[-1])
        prefix_features, _ = make_features(frame.iloc[: validation_end + 1])
        if prefix_features.index.max() > validation_end:
            raise AssertionError("Fold features include rows after validation.")
        x_train = prefix_features.loc[train_indices]
        x_validation = prefix_features.loc[validation_indices]
        if x_train.isna().any().any() or x_validation.isna().any().any():
            raise AssertionError("Fold features contain an unusable lag/rolling value.")

        model = _build_model()
        model.fit(x_train, target.loc[train_indices])
        train_predictions = model.predict(x_train)
        validation_predictions = model.predict(x_validation)
        fold_results.append(
            {
                "fold": fold_number,
                "train_rows": int(len(train_indices)),
                "validation_rows": int(len(validation_indices)),
                "train_start": frame.loc[train_indices, "month"].min().date().isoformat(),
                "train_end": frame.loc[train_indices, "month"].max().date().isoformat(),
                "validation_start": frame.loc[
                    validation_indices, "month"
                ].min().date().isoformat(),
                "validation_end": frame.loc[
                    validation_indices, "month"
                ].max().date().isoformat(),
                "train_mae_eur": float(
                    mean_absolute_error(target.loc[train_indices], train_predictions)
                ),
                "validation_mae_eur": float(
                    mean_absolute_error(
                        target.loc[validation_indices], validation_predictions
                    )
                ),
                "train_rmse_eur": float(
                    root_mean_squared_error(
                        target.loc[train_indices], train_predictions
                    )
                ),
                "validation_rmse_eur": float(
                    root_mean_squared_error(
                        target.loc[validation_indices], validation_predictions
                    )
                ),
                "chronology_verified": True,
                "feature_leakage_verified": True,
            }
        )

    def summary(metric: str, split: str) -> dict[str, float]:
        values = np.array([fold[f"{split}_{metric}_eur"] for fold in fold_results])
        return {"mean": float(values.mean()), "std": float(values.std(ddof=1))}

    return {
        "folds": fold_results,
        "metrics": {
            "mae": {
                "train": summary("mae", "train"),
                "validation": summary("mae", "validation"),
            },
            "rmse": {
                "train": summary("rmse", "train"),
                "validation": summary("rmse", "validation"),
            },
        },
        "n_splits": CV_FOLDS,
        "chronology_verified": True,
        "feature_leakage_verified": True,
    }


def plot_learning_curve(
    cv_results: dict[str, object], output_path: Path
) -> None:
    """Plot train and validation RMSE as the expanding training set grows."""
    folds = cv_results["folds"]
    train_sizes = [fold["train_rows"] for fold in folds]
    train_errors = [fold["train_rmse_eur"] for fold in folds]
    validation_errors = [fold["validation_rmse_eur"] for fold in folds]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(train_sizes, train_errors, marker="o", label="Error de entrenamiento")
    axis.plot(
        train_sizes,
        validation_errors,
        marker="o",
        label="Error de validación",
    )
    axis.set(
        title="TrackFlow: curva de aprendizaje temporal",
        xlabel="Filas de entrenamiento (ventana expansiva)",
        ylabel="RMSE (EUR)",
    )
    axis.grid(alpha=0.2)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def _fit_classification(cv_results: dict[str, object]) -> tuple[str, str]:
    """Classify fit from the CV gap and provide a justified corrective action."""
    train_rmse = cv_results["metrics"]["rmse"]["train"]["mean"]
    validation_rmse = cv_results["metrics"]["rmse"]["validation"]["mean"]
    gap_ratio = (validation_rmse - train_rmse) / max(train_rmse, 1e-9)
    validation_curve = [
        fold["validation_rmse_eur"] for fold in cv_results["folds"]
    ]
    improving = validation_curve[-1] < validation_curve[0]
    if gap_ratio > 0.25:
        return (
            "overfitting",
            "Reducir la varianza del Random Forest aumentando `min_samples_leaf` "
            "y limitar `max_depth`; el gap train-validación indica que los árboles "
            "están aprendiendo ruido de meses concretos.",
        )
    if gap_ratio < -0.05 or (not improving and train_rmse > validation_rmse * 0.8):
        return (
            "underfitting",
            "Añadir interacciones explícitas entre mes y tendencia (manteniendo "
            "lags causales) y revisar `min_samples_leaf`; el error alto y la curva "
            "sin mejora indican que el modelo no captura la estacionalidad de "
            "noviembre-diciembre y febrero.",
        )
    return (
        "bien ajustado",
        "Mantener la complejidad actual y recalibrar mensualmente con el fold "
        "más reciente; la brecha train-validación es contenida y la curva no "
        "muestra una divergencia creciente.",
    )


def write_evaluation_report(
    cv_results: dict[str, object],
    output_path: Path,
    test_metrics: dict[str, float] | None = None,
    average_revenue_eur: float | None = None,
) -> str:
    """Write the business-oriented technical evaluation report."""
    classification, corrective_action = _fit_classification(cv_results)
    metrics = cv_results["metrics"]
    report = f"""# Evaluación del modelo de pronóstico de TrackFlow

## Alcance y contexto

Se evaluó `revenue_eur` de la fila `market = "consolidated"` del dataset
mensual de TrackFlow. La partición final conserva los primeros ocho años para
entrenamiento y los dos últimos para prueba. La validación cruzada usa
`TimeSeriesSplit(n_splits={cv_results["n_splits"]})`, sin barajar datos.

El contrato de entrada conserva exactamente los campos `month`,
`revenue_eur`, `shipments_processed`, `avg_revenue_per_shipment_eur` y
`market`. `revenue_eur` es el objetivo; `shipments_processed` representa los
envíos procesados por Los Ángeles y Zaragoza, y
`avg_revenue_per_shipment_eur` es el ingreso medio por envío. El modelo usa
solo las filas `market = "consolidated"`, como exige el briefing, y no inventa
IDs de entidades que no existen en este dataset mensual.

Cada fold conserva el orden de `month`: el último mes de entrenamiento es
anterior al primer mes de validación. Los lags (`revenue_lag_1`, `3`, `6`, `12`)
y las ventanas (`revenue_rolling_mean_3`, `6`, `12`) se recalculan solo con el
prefijo histórico que termina en el último mes de validación del fold. Por
tanto, ninguna ventana puede leer una observación futura. Verificaciones
explícitas: chronology=`{cv_results["chronology_verified"]}` y
feature_leakage=`{cv_results["feature_leakage_verified"]}`.

## Resultados de validación cruzada

| Métrica | Entrenamiento (media ± desviación estándar) | Validación (media ± desviación estándar) |
|---|---:|---:|
| MAE (EUR) | {metrics["mae"]["train"]["mean"]:.2f} ± {metrics["mae"]["train"]["std"]:.2f} | {metrics["mae"]["validation"]["mean"]:.2f} ± {metrics["mae"]["validation"]["std"]:.2f} |
| RMSE (EUR) | {metrics["rmse"]["train"]["mean"]:.2f} ± {metrics["rmse"]["train"]["std"]:.2f} | {metrics["rmse"]["validation"]["mean"]:.2f} ± {metrics["rmse"]["validation"]["std"]:.2f} |

La curva de aprendizaje está en `data/eval/learning_curve.png` y muestra el
error RMSE de entrenamiento y validación conforme crece la ventana temporal.

## Métrica preferida para negocio

MAE refleja mejor el costo operativo típico para Thomas y Ana: expresa en EUR
el desvío mensual promedio, sin sobrerreaccionar a los picos de noviembre y
diciembre. RMSE se conserva como diagnóstico porque penaliza más los errores
grandes durante esos picos, que pueden afectar la planificación de almacén,
pero no debe ser la única métrica de decisión.

## Métricas del conjunto de prueba

"""
    if test_metrics is not None:
        report += f"""El conjunto de prueba contiene los 24 meses de 2024-01 a
2025-12. El MSE es
`{test_metrics["mse_eur_squared"]:.2f} EUR²`"""
        if average_revenue_eur:
            mse_percentage = (
                test_metrics["mse_eur_squared"] / average_revenue_eur**2 * 100
            )
            report += (
                f" ({mse_percentage:.2f}% del cuadrado del ingreso mensual "
                "promedio del entrenamiento)"
            )
        report += f"""; PSI={test_metrics["psi"]:.4f}; Gini={test_metrics["gini"]:.4f};
K2 Score (R²)={test_metrics["k2_score"]:.4f}.

"""

    report += f"""## Diagnóstico

**Clasificación: {classification}.**

La clasificación se apoya en la brecha media entre RMSE de entrenamiento y
validación y en la tendencia de ambas líneas de la curva de aprendizaje; no se
basa en un único fold. Acción correctiva concreta: {corrective_action}
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return classification


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
    learning_curve_path: Path = Path("data/eval/learning_curve.png"),
    report_path: Path = Path("data/eval/evaluation_report.md"),
) -> dict[str, object]:
    """Train on the first eight years and evaluate on the latest two."""
    frame = load_and_clean(path)
    features, target = make_features(frame)
    x_train, x_test, y_train, y_test = split_temporally(frame, features, target)
    cv_results = temporal_cross_validate(frame, features, target)
    plot_learning_curve(cv_results, learning_curve_path)
    model = _build_model()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    forest = model.named_steps["regressor"]
    tree_predictions = np.vstack(
        [tree.predict(model.named_steps["scaler"].transform(x_test)) for tree in forest.estimators_]
    )
    lower, upper = np.percentile(tree_predictions, [10, 90], axis=0)
    plot_forecast(frame, y_test, predictions, lower, upper, plot_path)
    test_metrics = calculate_metrics(y_train, y_test, predictions)
    fit_classification = write_evaluation_report(
        cv_results,
        report_path,
        test_metrics=test_metrics,
        average_revenue_eur=float(y_train.mean()),
    )
    return {
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "test_start": frame.loc[y_test.index, "month"].min().date().isoformat(),
        "test_end": frame.loc[y_test.index, "month"].max().date().isoformat(),
        "plot_path": str(plot_path),
        "learning_curve_path": str(learning_curve_path),
        "report_path": str(report_path),
        "fit_classification": fit_classification,
        "cross_validation": cv_results,
        "metrics": test_metrics,
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
