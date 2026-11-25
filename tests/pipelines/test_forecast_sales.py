from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.forecast_sales import make_features, split_temporally


def test_forecast_split_uses_eight_years_and_has_no_leakage():
    months = pd.date_range("2016-01-01", periods=120, freq="MS")
    frame = pd.DataFrame(
        {
            "month": months,
            "revenue_eur": np.arange(1000, 1120, dtype=float),
            "shipments_processed": np.arange(500, 620, dtype=float),
            "avg_revenue_per_shipment_eur": np.full(120, 2.0),
        }
    )
    features, target = make_features(frame)

    x_train, x_test, y_train, y_test = split_temporally(frame, features, target)

    assert len(x_train) == 84
    assert len(x_test) == 24
    assert set(y_train.index).isdisjoint(y_test.index)
    assert frame.loc[y_train.index, "month"].max() < pd.Timestamp("2024-01-01")
    assert frame.loc[y_test.index, "month"].min() >= pd.Timestamp("2024-01-01")
