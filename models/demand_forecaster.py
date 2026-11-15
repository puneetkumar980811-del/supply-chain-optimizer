"""
Demand Forecasting & Predictive Planning Module for Supply Chain Optimization.
Algorithms:
    1. Simple Moving Average (SMA)
    2. Exponential Smoothing (SES & Holt's Double Exponential Trend)
    3. Linear Trend Regression
    4. Accuracy Metrics: MAE, RMSE, MAPE
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def calculate_forecast_metrics(actual, predicted):
    """Computes MAE, RMSE, and MAPE error metrics."""
    actual = np.array(actual)
    predicted = np.array(predicted)
    valid_idx = ~np.isnan(actual) & ~np.isnan(predicted)

    if np.sum(valid_idx) == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}

    act = actual[valid_idx]
    pred = predicted[valid_idx]

    mae = float(np.mean(np.abs(act - pred)))
    rmse = float(np.sqrt(np.mean((act - pred) ** 2)))
    # Avoid zero division
    non_zero = act != 0
    mape = float(np.mean(np.abs((act[non_zero] - pred[non_zero]) / act[non_zero])) * 100.0) if np.any(non_zero) else 0.0

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


def simple_moving_average(series, window=3, forecast_periods=3):
    """Computes Simple Moving Average and projects future periods."""
    values = list(series)
    fitted = [np.nan] * (window - 1)
    for i in range(window - 1, len(values)):
        fitted.append(float(np.mean(values[i - window + 1: i + 1])))

    # Forecast future periods (constant value equal to last window mean)
    future = [float(np.mean(values[-window:]))] * forecast_periods
    return fitted, future


def exponential_smoothing(series, alpha=0.3, forecast_periods=3):
    """
    Single Exponential Smoothing (SES).
    S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
    """
    values = list(series)
    fitted = [values[0]]
    for t in range(1, len(values)):
        s_prev = fitted[-1]
        s_curr = alpha * values[t] + (1 - alpha) * s_prev
        fitted.append(s_curr)

    # Future forecast is constant level
    future = [fitted[-1]] * forecast_periods
    return fitted, future


def holt_linear_trend(series, alpha=0.3, beta=0.1, forecast_periods=3):
    """
    Holt's Double Exponential Smoothing for data with trend.
    Level: L_t = alpha * Y_t + (1 - alpha) * (L_{t-1} + T_{t-1})
    Trend: T_t = beta * (L_t - L_{t-1}) + (1 - beta) * T_{t-1}
    Forecast: Y_{t+m} = L_t + m * T_t
    """
    values = list(series)
    if len(values) < 2:
        return values, [values[0]] * forecast_periods

    l = [values[0]]
    b = [values[1] - values[0]]
    fitted = [values[0]]

    for t in range(1, len(values)):
        y_t = values[t]
        l_prev = l[-1]
        b_prev = b[-1]

        l_curr = alpha * y_t + (1 - alpha) * (l_prev + b_prev)
        b_curr = beta * (l_curr - l_prev) + (1 - beta) * b_prev

        l.append(l_curr)
        b.append(b_curr)
        fitted.append(l_prev + b_prev)

    # Future forecast
    future = []
    for m in range(1, forecast_periods + 1):
        future.append(float(l[-1] + m * b[-1]))

    return fitted, future


def linear_trend_regression(series, forecast_periods=3):
    """Fits an Ordinary Least Squares (OLS) linear trend line and projects future."""
    y = np.array(series)
    X = np.arange(len(y)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(X, y)

    fitted = model.predict(X).tolist()

    X_future = np.arange(len(y), len(y) + forecast_periods).reshape(-1, 1)
    future = model.predict(X_future).tolist()

    return fitted, future, model.coef_[0], model.intercept_


def run_comprehensive_forecast(df, demand_col="Demand", time_col="Month", forecast_periods=6):
    """
    Runs all candidate forecasting models, computes error benchmarks,
    and returns a combined dataframe with best model projection and confidence intervals.
    """
    actual = df[demand_col].values
    n = len(actual)

    sma_fit, sma_future = simple_moving_average(actual, window=3, forecast_periods=forecast_periods)
    ses_fit, ses_future = exponential_smoothing(actual, alpha=0.35, forecast_periods=forecast_periods)
    holt_fit, holt_future = holt_linear_trend(actual, alpha=0.35, beta=0.15, forecast_periods=forecast_periods)
    lr_fit, lr_future, slope, intercept = linear_trend_regression(actual, forecast_periods=forecast_periods)

    metrics = {
        "Simple Moving Avg (3M)": calculate_forecast_metrics(actual[2:], sma_fit[2:]),
        "Single Exp Smoothing": calculate_forecast_metrics(actual, ses_fit),
        "Holt's Linear Trend": calculate_forecast_metrics(actual, holt_fit),
        "Linear Regression": calculate_forecast_metrics(actual, lr_fit),
    }

    metrics_df = pd.DataFrame(metrics).T
    metrics_df = metrics_df.sort_values(by="mape")

    best_model_name = metrics_df.index[0]
    best_forecast_map = {
        "Simple Moving Avg (3M)": (sma_fit, sma_future),
        "Single Exp Smoothing": (ses_fit, ses_future),
        "Holt's Linear Trend": (holt_fit, holt_future),
        "Linear Regression": (lr_fit, lr_future),
    }
    best_fit, best_future = best_forecast_map[best_model_name]

    # Calculate residual std dev for confidence intervals
    residuals = actual - np.array(best_fit)
    std_err = float(np.std(residuals))

    # Build historical + forecast timeline
    future_labels = [f"Forecast M+{i+1}" for i in range(forecast_periods)]
    all_time = list(df[time_col]) + future_labels

    all_actual = list(actual) + [np.nan] * forecast_periods
    all_best_pred = list(best_fit) + list(best_future)

    ci_upper = [np.nan] * n + [val + 1.96 * std_err for val in best_future]
    ci_lower = [np.nan] * n + [max(0.0, val - 1.96 * std_err) for val in best_future]

    result_df = pd.DataFrame({
        "Period": all_time,
        "Actual_Demand": all_actual,
        "Best_Forecast": np.round(all_best_pred, 1),
        "SMA_3M": sma_fit + sma_future,
        "SES": np.round(ses_fit + ses_future, 1),
        "Holt_Trend": np.round(holt_fit + holt_future, 1),
        "Linear_Regression": np.round(lr_fit + lr_future, 1),
        "CI_Upper_95": np.round(ci_upper, 1),
        "CI_Lower_95": np.round(ci_lower, 1),
    })

    return {
        "metrics_df": metrics_df,
        "best_model_name": best_model_name,
        "result_df": result_df,
        "projected_demand": round(float(np.mean(best_future)), 1),
        "annual_projected_demand": round(float(np.mean(best_future) * 12), 1),
    }
