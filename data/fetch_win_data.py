import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import MetaTrader5 as mt5


SYMBOL = "WIN$N"
YEARS = 4
CHUNK_DAYS = 90
SAVE_DIR = Path("raw")

TIMEFRAMES = {
    "D1": mt5.TIMEFRAME_D1,
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
    "M30": mt5.TIMEFRAME_M30,
    "M15": mt5.TIMEFRAME_M15,
    "M5": mt5.TIMEFRAME_M5,
}


def save(timeframe_name, columns, rows):
    SAVE_DIR.mkdir(exist_ok=True)
    path = SAVE_DIR / f"WIN_{timeframe_name}.csv"

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    return path


def years_ago(years):
    now = datetime.now(timezone.utc)
    try:
        return now.replace(year=now.year - years), now
    except ValueError:
        return now.replace(year=now.year - years, day=28), now


def get_rates(symbol, timeframe, start, end):
    current = start
    columns = None
    rows = []
    seen_times = set()

    while current < end:
        next_date = min(current + timedelta(days=CHUNK_DAYS), end)
        rates = mt5.copy_rates_range(symbol, timeframe, current, next_date)

        if rates is not None and len(rates) > 0:
            columns = rates.dtype.names

            for row in rates.tolist():
                candle_time = row[0]
                if candle_time not in seen_times:
                    seen_times.add(candle_time)
                    rows.append(row)

        current = next_date

    return columns, rows


def get_candles(symbol=SYMBOL, years=YEARS):
    if not mt5.initialize():
        raise RuntimeError(f"Erro ao conectar no MT5: {mt5.last_error()}")

    try:
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"Simbolo nao encontrado ou indisponivel: {symbol}")

        start, end = years_ago(years)
        files = []

        for name, timeframe in TIMEFRAMES.items():
            columns, rows = get_rates(symbol, timeframe, start, end)

            if not rows:
                print(f"{name}: nenhum candle retornado. Erro MT5: {mt5.last_error()}")
                continue

            path = save(name, columns, rows)
            files.append(path)

            print(f"{name}: {len(rows)} candles salvos em {path}.")

        return files
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    get_candles()
