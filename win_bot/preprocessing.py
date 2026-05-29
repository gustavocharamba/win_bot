from __future__ import annotations

from pathlib import Path

import pandas as pd

from win_bot.gap_features import GAP_COLUMNS, add_gap_features, get_time_gaps


DATA_DIR = Path("data")
MARKET_TIMEZONE = "America/Sao_Paulo"

CSV_FILES = {
    "D1": "WIN_D1",
    "H4": "WIN_H4",
    "H1": "WIN_H1",
    "M30": "WIN_M30",
    "M15": "WIN_M15",
    "M5": "WIN_M5",
}

MT5_COLUMNS = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]

BASE_COLUMNS = [
    "time",
    "datetime",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]

FINAL_COLUMNS = [*BASE_COLUMNS, *GAP_COLUMNS]


def empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=FINAL_COLUMNS).astype(
        {
            "has_time_gap": bool,
            "is_session_start": bool,
        }
    )


def resolve_csv(name: str) -> Path | None:
    path = DATA_DIR / name
    candidates = [path, path.with_suffix(".csv")]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def load_csv(timeframe: str) -> pd.DataFrame:
    path = resolve_csv(CSV_FILES[timeframe])

    if path is None:
        return empty_frame()

    df = pd.read_csv(path)
    validate_mt5_columns(df, path)

    df = normalize_mt5_dataframe(df, timeframe)
    df = add_gap_features(df, timeframe)

    return df[FINAL_COLUMNS]


def validate_mt5_columns(df: pd.DataFrame, path: Path) -> None:
    missing_columns = [column for column in MT5_COLUMNS if column not in df.columns]

    if missing_columns:
        raise ValueError(f"{path} sem colunas do MT5: {missing_columns}")


def normalize_mt5_dataframe(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df = df.copy()
    df["time"] = pd.to_numeric(df["time"])
    df["datetime"] = (
        pd.to_datetime(df["time"], unit="s", utc=True)
        .dt.tz_convert(MARKET_TIMEZONE)
        .dt.tz_localize(None)
    )
    df["timeframe"] = timeframe

    df = df.sort_values("datetime")
    df = df.drop_duplicates(subset="datetime", keep="last")
    df = df.reset_index(drop=True)

    return df


def prepare_timeframe(timeframe: str) -> pd.DataFrame:
    return load_csv(timeframe)


df_1d = prepare_timeframe("D1")
df_4h = prepare_timeframe("H4")
df_1h = prepare_timeframe("H1")
df_30m = prepare_timeframe("M30")
df_15m = prepare_timeframe("M15")
df_5m = prepare_timeframe("M5")

time_gaps = {
    "D1": get_time_gaps(df_1d),
    "H4": get_time_gaps(df_4h),
    "H1": get_time_gaps(df_1h),
    "M30": get_time_gaps(df_30m),
    "M15": get_time_gaps(df_15m),
    "M5": get_time_gaps(df_5m),
}
