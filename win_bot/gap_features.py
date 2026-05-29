from __future__ import annotations

import pandas as pd


EXPECTED_MINUTES = {
    "D1": 24 * 60,
    "H4": 4 * 60,
    "H1": 60,
    "M30": 30,
    "M15": 15,
    "M5": 5,
}

GAP_COLUMNS = [
    "minutes_since_prev",
    "expected_minutes",
    "has_time_gap",
    "is_session_start",
    "gap_points",
    "gap_pct",
]


def add_gap_features(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Measure market gaps without creating artificial candles.

    Para ML tabular, nao preenchemos gaps normais do mercado com candles
    artificiais. Abertura de pregao, fim de semana, feriado e pausas fazem
    parte do mercado. O modelo recebe essa informacao como feature, nao como
    candle inventado.
    """
    if df.empty:
        return df

    if timeframe not in EXPECTED_MINUTES:
        raise ValueError(f"timeframe sem intervalo esperado: {timeframe}")

    df = df.copy()
    expected_minutes = EXPECTED_MINUTES[timeframe]

    df["minutes_since_prev"] = df["datetime"].diff().dt.total_seconds().div(60)
    df["expected_minutes"] = expected_minutes
    df["has_time_gap"] = df["minutes_since_prev"] > expected_minutes
    df["is_session_start"] = df["datetime"].dt.date != df["datetime"].shift().dt.date

    previous_close = df["close"].shift()
    df["gap_points"] = df["open"] - previous_close
    df["gap_pct"] = df["gap_points"] / previous_close.where(previous_close != 0)

    return df


def get_time_gaps(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["has_time_gap"]].copy()
