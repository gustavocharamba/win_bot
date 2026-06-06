from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REPORT_DIR = PROJECT_ROOT / "reports" / "data_quality"

MARKET_TIMEZONE = "America/Sao_Paulo"

TIMEFRAMES = {
    "D1": 24 * 60,
    "H4": 4 * 60,
    "H1": 60,
    "M30": 30,
    "M15": 15,
    "M5": 5,
}

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

PROCESSED_COLUMNS = [
    "time",
    "datetime",
    "datetime_market",
    "datetime_utc_to_market",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
    "minutes_since_prev",
    "expected_minutes",
    "has_time_gap",
    "is_session_start",
    "gap_points",
    "gap_pct",
    "gap_abs",
    "gap_direction",
]

OFFICIAL_START = time(9, 0)
OFFICIAL_END = time(18, 25)
DECISION_START = time(10, 0)
DECISION_END = time(16, 30)

OPERATIONAL_WINDOWS = [
    ("official_session", "Sessao oficial de referencia", time(9, 0), time(18, 25)),
    ("opening_block", "Abertura bloqueada v1", time(9, 0), time(10, 0)),
    ("decision_window", "Janela de decisao v1", time(10, 0), time(16, 30)),
    ("stop_new_entries", "Parar novas entradas", time(16, 30), None),
    ("flat_deadline", "Zeragem simulada inicial", time(17, 0), None),
    ("settlement_window", "Janela de ajuste B3", time(17, 0), time(17, 15)),
]


def pct(value: int | float, total: int | float) -> float:
    if total == 0:
        return 0.0
    return round(float(value) / float(total) * 100, 4)


def as_percent(mask: pd.Series) -> float:
    if len(mask) == 0:
        return 0.0
    return round(float(mask.mean()) * 100, 4)


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sem dados."

    headers = [str(column) for column in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for _, row in df.iterrows():
        values = [fmt(row[column]).replace("\n", " ") for column in df.columns]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def fmt_time(value: time | None) -> str:
    if value is None:
        return ""
    return value.strftime("%H:%M")


def operational_windows() -> pd.DataFrame:
    rows = []

    for name, description, start, end in OPERATIONAL_WINDOWS:
        rows.append(
            {
                "name": name,
                "description": description,
                "market_time_start": fmt_time(start),
                "market_time_end": fmt_time(end),
                "datetime_market_start": fmt_time(start),
                "datetime_market_end": fmt_time(end),
            }
        )

    return pd.DataFrame(rows)


def dt_utc_to_market(raw_time: pd.Series) -> pd.Series:
    return (
        pd.to_datetime(raw_time, unit="s", utc=True)
        .dt.tz_convert(MARKET_TIMEZONE)
        .dt.tz_localize(None)
    )


def dt_raw_clock(raw_time: pd.Series) -> pd.Series:
    return pd.to_datetime(raw_time, unit="s")


def time_mask(dt: pd.Series, start: time, end: time) -> pd.Series:
    clock = dt.dt.time
    return (clock >= start) & (clock <= end)


def numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def raw_path(timeframe: str) -> Path:
    return RAW_DATA_DIR / f"{CSV_FILES[timeframe]}.csv"


def processed_path(timeframe: str) -> Path:
    return PROCESSED_DATA_DIR / f"{CSV_FILES[timeframe]}_processed.csv"


def choose_time_interpretation(
    timeframe: str,
    utc_market_official_pct: float,
    raw_clock_official_pct: float,
) -> str:
    if timeframe == "D1":
        return "raw_clock_daily"

    if raw_clock_official_pct >= 95 and (
        raw_clock_official_pct - utc_market_official_pct
    ) >= 15:
        return "raw_clock"

    if utc_market_official_pct >= 95 and (
        utc_market_official_pct - raw_clock_official_pct
    ) >= 15:
        return "utc_to_market"

    return "review"


def load_raw(timeframe: str) -> pd.DataFrame | None:
    path = raw_path(timeframe)
    if not path.exists():
        return None
    return pd.read_csv(path)


def raw_summary(timeframe: str, df: pd.DataFrame | None) -> dict[str, Any]:
    expected_minutes = TIMEFRAMES[timeframe]
    path = raw_path(timeframe)

    if df is None:
        return {
            "timeframe": timeframe,
            "raw_exists": False,
            "raw_file": str(path.relative_to(PROJECT_ROOT)),
            "rows": 0,
            "decision": "block_missing_raw",
        }

    missing_columns = [column for column in MT5_COLUMNS if column not in df.columns]
    raw_time = numeric_column(df, "time")
    valid_time = raw_time.notna()
    rows = len(df)

    if valid_time.any():
        utc_market_dt = dt_utc_to_market(raw_time[valid_time])
        raw_clock_dt = dt_raw_clock(raw_time[valid_time])
    else:
        utc_market_dt = pd.Series(dtype="datetime64[ns]")
        raw_clock_dt = pd.Series(dtype="datetime64[ns]")

    if timeframe == "D1":
        utc_market_official_pct = None
        raw_clock_official_pct = None
        utc_market_decision_pct = None
        raw_clock_decision_pct = None
    else:
        utc_market_official_pct = as_percent(
            time_mask(utc_market_dt, OFFICIAL_START, OFFICIAL_END)
        )
        raw_clock_official_pct = as_percent(
            time_mask(raw_clock_dt, OFFICIAL_START, OFFICIAL_END)
        )
        utc_market_decision_pct = as_percent(
            time_mask(utc_market_dt, DECISION_START, DECISION_END)
        )
        raw_clock_decision_pct = as_percent(
            time_mask(raw_clock_dt, DECISION_START, DECISION_END)
        )

    interpretation = choose_time_interpretation(
        timeframe,
        utc_market_official_pct or 0.0,
        raw_clock_official_pct or 0.0,
    )

    analysis_dt = raw_clock_dt
    sorted_time = raw_time[valid_time].sort_values()
    sorted_dt = dt_raw_clock(sorted_time)
    minutes_since_prev = sorted_dt.diff().dt.total_seconds().div(60)
    gap_mask = minutes_since_prev > expected_minutes

    open_ = numeric_column(df, "open")
    high = numeric_column(df, "high")
    low = numeric_column(df, "low")
    close = numeric_column(df, "close")
    spread = numeric_column(df, "spread")
    real_volume = numeric_column(df, "real_volume")
    tick_volume = numeric_column(df, "tick_volume")

    high_low_anomalies = int((high < low).sum())
    high_price_anomalies = int((high < pd.concat([open_, close], axis=1).max(axis=1)).sum())
    low_price_anomalies = int((low > pd.concat([open_, close], axis=1).min(axis=1)).sum())
    non_positive_price_rows = int(((open_ <= 0) | (high <= 0) | (low <= 0) | (close <= 0)).sum())

    return {
        "timeframe": timeframe,
        "raw_exists": True,
        "raw_file": str(path.relative_to(PROJECT_ROOT)),
        "file_size_bytes": path.stat().st_size,
        "rows": rows,
        "valid_time_rows": int(valid_time.sum()),
        "missing_columns": ";".join(missing_columns),
        "duplicate_time_rows": int(raw_time.duplicated().sum()),
        "normalized_unique_time_rows": int(raw_time.dropna().drop_duplicates().shape[0]),
        "first_utc_to_market": utc_market_dt.min() if len(utc_market_dt) else None,
        "last_utc_to_market": utc_market_dt.max() if len(utc_market_dt) else None,
        "first_raw_clock": raw_clock_dt.min() if len(raw_clock_dt) else None,
        "last_raw_clock": raw_clock_dt.max() if len(raw_clock_dt) else None,
        "unique_days_raw_clock": int(analysis_dt.dt.date.nunique()) if len(analysis_dt) else 0,
        "utc_market_official_pct": utc_market_official_pct,
        "raw_clock_official_pct": raw_clock_official_pct,
        "utc_market_decision_pct": utc_market_decision_pct,
        "raw_clock_decision_pct": raw_clock_decision_pct,
        "recommended_time_interpretation": interpretation,
        "gap_rows": int(gap_mask.sum()),
        "gap_rows_pct": pct(int(gap_mask.sum()), len(minutes_since_prev)),
        "max_minutes_since_prev": round(float(minutes_since_prev.max()), 4)
        if minutes_since_prev.notna().any()
        else None,
        "real_volume_zero_pct": as_percent(real_volume.fillna(0) == 0),
        "tick_volume_zero_pct": as_percent(tick_volume.fillna(0) == 0),
        "spread_mean": round(float(spread.mean()), 4) if spread.notna().any() else None,
        "spread_p95": round(float(spread.quantile(0.95)), 4)
        if spread.notna().any()
        else None,
        "spread_max": round(float(spread.max()), 4) if spread.notna().any() else None,
        "spread_negative_rows": int((spread < 0).sum()),
        "high_low_anomalies": high_low_anomalies,
        "high_price_anomalies": high_price_anomalies,
        "low_price_anomalies": low_price_anomalies,
        "non_positive_price_rows": non_positive_price_rows,
        "decision": "review",
    }


def daily_counts(timeframe: str, df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or "time" not in df.columns:
        return pd.DataFrame()

    raw_time = numeric_column(df, "time").dropna()
    dt = dt_raw_clock(raw_time)
    out = (
        pd.DataFrame({"date": dt.dt.date})
        .groupby("date")
        .size()
        .reset_index(name="rows")
    )
    out.insert(0, "timeframe", timeframe)
    return out


def hourly_profile(timeframe: str, df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or "time" not in df.columns:
        return pd.DataFrame()

    rows = []
    raw_time = numeric_column(df, "time")
    valid = raw_time.notna()
    spread = numeric_column(df.loc[valid], "spread")
    tick_volume = numeric_column(df.loc[valid], "tick_volume")
    real_volume = numeric_column(df.loc[valid], "real_volume")

    for name, dt in {
        "utc_to_market": dt_utc_to_market(raw_time[valid]),
        "raw_clock": dt_raw_clock(raw_time[valid]),
    }.items():
        tmp = pd.DataFrame(
            {
                "hour": dt.dt.hour,
                "spread": spread.to_numpy(),
                "tick_volume": tick_volume.to_numpy(),
                "real_volume": real_volume.to_numpy(),
            }
        )
        grouped = tmp.groupby("hour")
        for hour, group in grouped:
            rows.append(
                {
                    "timeframe": timeframe,
                    "interpretation": name,
                    "hour": int(hour),
                    "rows": int(len(group)),
                    "spread_mean": round(float(group["spread"].mean()), 4),
                    "spread_p95": round(float(group["spread"].quantile(0.95)), 4),
                    "tick_volume_mean": round(float(group["tick_volume"].mean()), 4),
                    "real_volume_zero_pct": as_percent(group["real_volume"].fillna(0) == 0),
                }
            )

    return pd.DataFrame(rows)


def gap_extremes(timeframe: str, df: pd.DataFrame | None, limit: int = 25) -> pd.DataFrame:
    if df is None or "time" not in df.columns:
        return pd.DataFrame()

    expected_minutes = TIMEFRAMES[timeframe]
    raw_time = numeric_column(df, "time")
    valid = raw_time.notna()
    tmp = df.loc[valid].copy()
    tmp["time"] = raw_time[valid]
    tmp = tmp.sort_values("time").drop_duplicates(subset="time", keep="last")
    tmp["datetime_raw_clock"] = dt_raw_clock(tmp["time"])
    tmp["datetime_utc_to_market"] = dt_utc_to_market(tmp["time"])
    tmp["prev_datetime_raw_clock"] = tmp["datetime_raw_clock"].shift()
    tmp["minutes_since_prev"] = (
        tmp["datetime_raw_clock"].diff().dt.total_seconds().div(60)
    )
    tmp["expected_minutes"] = expected_minutes
    tmp["has_time_gap"] = tmp["minutes_since_prev"] > expected_minutes
    tmp["prev_close"] = numeric_column(tmp, "close").shift()
    tmp["gap_points"] = numeric_column(tmp, "open") - tmp["prev_close"]

    cols = [
        "timeframe",
        "datetime_raw_clock",
        "datetime_utc_to_market",
        "prev_datetime_raw_clock",
        "minutes_since_prev",
        "expected_minutes",
        "open",
        "prev_close",
        "gap_points",
    ]
    tmp.insert(0, "timeframe", timeframe)
    return (
        tmp.loc[tmp["has_time_gap"], cols]
        .sort_values("minutes_since_prev", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def processed_comparison(timeframe: str, raw_df: pd.DataFrame | None) -> dict[str, Any]:
    path = processed_path(timeframe)
    raw_rows = 0
    raw_unique_time_rows = 0
    if raw_df is not None and "time" in raw_df.columns:
        raw_time = numeric_column(raw_df, "time")
        raw_rows = len(raw_df)
        raw_unique_time_rows = int(raw_time.dropna().drop_duplicates().shape[0])

    if not path.exists():
        return {
            "timeframe": timeframe,
            "processed_exists": False,
            "processed_file": str(path.relative_to(PROJECT_ROOT)),
            "raw_rows": raw_rows,
            "raw_unique_time_rows": raw_unique_time_rows,
        }

    df = pd.read_csv(path)
    missing_columns = [column for column in PROCESSED_COLUMNS if column not in df.columns]
    datetime_column = "datetime_market" if "datetime_market" in df.columns else "datetime"
    dt = (
        pd.to_datetime(df[datetime_column], errors="coerce")
        if datetime_column in df.columns
        else pd.Series(dtype="datetime64[ns]")
    )

    if timeframe == "D1" or len(dt) == 0:
        official_pct = None
        decision_pct = None
    else:
        official_pct = as_percent(time_mask(dt.dropna(), OFFICIAL_START, OFFICIAL_END))
        decision_pct = as_percent(time_mask(dt.dropna(), DECISION_START, DECISION_END))

    duplicate_datetime_rows = (
        int(df[datetime_column].duplicated().sum()) if datetime_column in df.columns else None
    )

    return {
        "timeframe": timeframe,
        "processed_exists": True,
        "processed_file": str(path.relative_to(PROJECT_ROOT)),
        "processed_rows": len(df),
        "processed_columns": len(df.columns),
        "missing_processed_columns": ";".join(missing_columns),
        "raw_rows": raw_rows,
        "raw_unique_time_rows": raw_unique_time_rows,
        "row_delta_vs_raw_unique": len(df) - raw_unique_time_rows,
        "first_processed_datetime": dt.min() if len(dt) else None,
        "last_processed_datetime": dt.max() if len(dt) else None,
        "processed_datetime_column": datetime_column,
        "processed_official_pct": official_pct,
        "processed_decision_pct": decision_pct,
        "duplicate_datetime_rows": duplicate_datetime_rows,
    }


def summarize_daily_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return (
        df.groupby("timeframe")["rows"]
        .agg(["count", "min", "median", "max"])
        .reset_index()
        .rename(
            columns={
                "count": "days",
                "min": "min_rows_per_day",
                "median": "median_rows_per_day",
                "max": "max_rows_per_day",
            }
        )
    )


def build_markdown_report(
    raw_summary_df: pd.DataFrame,
    daily_summary_df: pd.DataFrame,
    processed_df: pd.DataFrame,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    blockers = []
    warnings = []

    if (raw_summary_df["raw_exists"] == False).any():  # noqa: E712
        blockers.append("Existe timeframe bruto ausente em data/raw.")

    processed_decision_timeframes = processed_df[
        processed_df["timeframe"].isin(["H1", "M30", "M15", "M5"])
    ]
    processed_timezone_issue = processed_decision_timeframes[
        processed_decision_timeframes["processed_official_pct"].fillna(0) < 95
    ]
    if not processed_timezone_issue.empty:
        blockers.append(
            "`datetime_market` dos processados nao encaixa em pelo menos 95% "
            "dos candles intraday dentro do horario oficial de referencia."
        )

    if (raw_summary_df["missing_columns"].fillna("") != "").any():
        blockers.append("Ha colunas obrigatorias do MT5 ausentes em algum CSV bruto.")

    if (raw_summary_df["duplicate_time_rows"].fillna(0).astype(int) > 0).any():
        warnings.append("Ha timestamps duplicados em dados brutos; o preprocessing remove duplicatas.")

    if (raw_summary_df["high_low_anomalies"].fillna(0).astype(int) > 0).any():
        blockers.append("Ha candles com high menor que low.")

    if (raw_summary_df["real_volume_zero_pct"].fillna(0) > 20).any():
        warnings.append("real_volume tem muitos zeros em pelo menos um timeframe.")

    if (processed_df["processed_exists"] == False).any():  # noqa: E712
        warnings.append("Nem todos os CSVs processados existem em data/processed.")

    if (processed_df["row_delta_vs_raw_unique"].fillna(0).astype(int) != 0).any():
        warnings.append("Ha diferenca de linhas entre raw unico e processed em algum timeframe.")

    if blockers:
        decision = "NAO APROVADO PARA FEATURES/LABELS"
    elif warnings:
        decision = "APROVADO COM RESSALVAS"
    else:
        decision = "APROVADO PARA FEATURES/LABELS"

    lines = [
        "# Data Quality Report v1",
        "",
        f"Gerado em: {generated_at}",
        "",
        f"Decisao: **{decision}**",
        "",
        "## Leitura executiva",
        "",
    ]

    if blockers:
        lines.append("Bloqueios:")
        for item in blockers:
            lines.append(f"- {item}")
        lines.append("")

    if warnings:
        lines.append("Ressalvas:")
        for item in warnings:
            lines.append(f"- {item}")
        lines.append("")

    if not blockers and not warnings:
        lines.append("- Nenhum bloqueio ou ressalva automatica foi detectado.")
        lines.append("")

    lines.extend(
        [
            "## Achado principal sobre timezone",
            "",
            "Nos dados atuais, a leitura do timestamp `time` como relogio de "
            "mercado (`raw_clock`) encaixa melhor nos horarios oficiais para "
            "H1/M30/M15/M5 do que a interpretacao UTC->America/Sao_Paulo. Por "
            "decisao do contrato v1, `datetime_market` e o horario canonico "
            "para pesquisa, features, labels e backtest. A coluna "
            "`datetime_utc_to_market` fica apenas para auditoria.",
            "",
            "## Horarios operacionais canonicos",
            "",
            markdown_table(operational_windows()),
            "",
            "## Resumo por timeframe",
            "",
            markdown_table(raw_summary_df[
                [
                    "timeframe",
                    "rows",
                    "first_utc_to_market",
                    "last_utc_to_market",
                    "first_raw_clock",
                    "last_raw_clock",
                    "utc_market_official_pct",
                    "raw_clock_official_pct",
                    "recommended_time_interpretation",
                    "gap_rows",
                    "real_volume_zero_pct",
                    "spread_mean",
                    "spread_p95",
                    "spread_max",
                ]
            ]),
            "",
            "## Candles por dia",
            "",
            markdown_table(daily_summary_df),
            "",
            "## Comparacao raw vs processed",
            "",
            markdown_table(processed_df[
                [
                    "timeframe",
                    "processed_exists",
                    "processed_rows",
                    "raw_unique_time_rows",
                    "row_delta_vs_raw_unique",
                    "processed_datetime_column",
                    "first_processed_datetime",
                    "last_processed_datetime",
                    "processed_official_pct",
                    "missing_processed_columns",
                ]
            ]),
            "",
            "## Proximas acoes recomendadas",
            "",
            "1. Usar `datetime_market` como unica coluna temporal canonica nas "
            "proximas features, labels e backtests.",
            "2. Manter `time` original e `datetime_utc_to_market` apenas para "
            "rastreabilidade/auditoria.",
            "3. Reexecutar este relatorio apos qualquer mudanca no preprocessing "
            "ou nos dados.",
            "4. So depois criar features v1 e labels.",
            "",
            "## Arquivos gerados",
            "",
            "- `reports/data_quality/raw_timeframe_summary.csv`",
            "- `reports/data_quality/daily_counts.csv`",
            "- `reports/data_quality/daily_counts_summary.csv`",
            "- `reports/data_quality/hourly_profile.csv`",
            "- `reports/data_quality/gap_extremes.csv`",
            "- `reports/data_quality/raw_processed_comparison.csv`",
            "- `reports/data_quality/operational_windows.csv`",
            "- `reports/data_quality/data_quality_report.md`",
        ]
    )

    return "\n".join(lines) + "\n"


def run_quality_report() -> dict[str, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    raw_frames = {timeframe: load_raw(timeframe) for timeframe in TIMEFRAMES}

    raw_summary_df = pd.DataFrame(
        [raw_summary(timeframe, raw_frames[timeframe]) for timeframe in TIMEFRAMES]
    )
    daily_counts_df = pd.concat(
        [daily_counts(timeframe, raw_frames[timeframe]) for timeframe in TIMEFRAMES],
        ignore_index=True,
    )
    daily_summary_df = summarize_daily_counts(daily_counts_df)
    hourly_profile_df = pd.concat(
        [hourly_profile(timeframe, raw_frames[timeframe]) for timeframe in TIMEFRAMES],
        ignore_index=True,
    )
    gap_extremes_df = pd.concat(
        [gap_extremes(timeframe, raw_frames[timeframe]) for timeframe in TIMEFRAMES],
        ignore_index=True,
    )
    processed_df = pd.DataFrame(
        [
            processed_comparison(timeframe, raw_frames[timeframe])
            for timeframe in TIMEFRAMES
        ]
    )
    operational_windows_df = operational_windows()

    outputs = {
        "raw_summary": REPORT_DIR / "raw_timeframe_summary.csv",
        "daily_counts": REPORT_DIR / "daily_counts.csv",
        "daily_summary": REPORT_DIR / "daily_counts_summary.csv",
        "hourly_profile": REPORT_DIR / "hourly_profile.csv",
        "gap_extremes": REPORT_DIR / "gap_extremes.csv",
        "processed_comparison": REPORT_DIR / "raw_processed_comparison.csv",
        "operational_windows": REPORT_DIR / "operational_windows.csv",
        "markdown_report": REPORT_DIR / "data_quality_report.md",
    }

    raw_summary_df.to_csv(outputs["raw_summary"], index=False)
    daily_counts_df.to_csv(outputs["daily_counts"], index=False)
    daily_summary_df.to_csv(outputs["daily_summary"], index=False)
    hourly_profile_df.to_csv(outputs["hourly_profile"], index=False)
    gap_extremes_df.to_csv(outputs["gap_extremes"], index=False)
    processed_df.to_csv(outputs["processed_comparison"], index=False)
    operational_windows_df.to_csv(outputs["operational_windows"], index=False)

    markdown = build_markdown_report(raw_summary_df, daily_summary_df, processed_df)
    outputs["markdown_report"].write_text(markdown, encoding="utf-8")

    return outputs


def main() -> None:
    outputs = run_quality_report()
    report = outputs["markdown_report"]
    print(f"Relatorio de qualidade gerado em {report}")


if __name__ == "__main__":
    main()
