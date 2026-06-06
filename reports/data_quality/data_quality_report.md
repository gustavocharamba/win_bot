# Data Quality Report v1

Gerado em: 2026-06-05 17:28:08

Decisao: **APROVADO PARA FEATURES/LABELS**

## Leitura executiva

- Nenhum bloqueio ou ressalva automatica foi detectado.

## Achado principal sobre timezone

Nos dados atuais, a leitura do timestamp `time` como relogio de mercado (`raw_clock`) encaixa melhor nos horarios oficiais para H1/M30/M15/M5 do que a interpretacao UTC->America/Sao_Paulo. Por decisao do contrato v1, `datetime_market` e o horario canonico para pesquisa, features, labels e backtest. A coluna `datetime_utc_to_market` fica apenas para auditoria.

## Horarios operacionais canonicos

| name | description | market_time_start | market_time_end | datetime_market_start | datetime_market_end |
| --- | --- | --- | --- | --- | --- |
| official_session | Sessao oficial de referencia | 09:00 | 18:25 | 09:00 | 18:25 |
| opening_block | Abertura bloqueada v1 | 09:00 | 10:00 | 09:00 | 10:00 |
| decision_window | Janela de decisao v1 | 10:00 | 16:30 | 10:00 | 16:30 |
| stop_new_entries | Parar novas entradas | 16:30 |  | 16:30 |  |
| flat_deadline | Zeragem simulada inicial | 17:00 |  | 17:00 |  |
| settlement_window | Janela de ajuste B3 | 17:00 | 17:15 | 17:00 | 17:15 |

## Resumo por timeframe

| timeframe | rows | first_utc_to_market | last_utc_to_market | first_raw_clock | last_raw_clock | utc_market_official_pct | raw_clock_official_pct | recommended_time_interpretation | gap_rows | real_volume_zero_pct | spread_mean | spread_p95 | spread_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | 997 | 2022-06-01 21:00:00 | 2026-05-31 21:00:00 | 2022-06-02 00:00:00 | 2026-06-01 00:00:00 |  |  | raw_clock_daily | 230 | 0.0000 | 4.9950 | 5.0000 | 5.0000 |
| H4 | 2987 | 2022-06-02 05:00:00 | 2026-06-01 13:00:00 | 2022-06-02 08:00:00 | 2026-06-01 16:00:00 | 66.7559 | 66.7559 | review | 996 | 0.0000 | 4.9950 | 5.0000 | 5.0000 |
| H1 | 9683 | 2022-06-02 06:00:00 | 2026-06-01 15:00:00 | 2022-06-02 09:00:00 | 2026-06-01 18:00:00 | 69.2347 | 100.0000 | raw_clock | 996 | 0.0000 | 4.9948 | 5.0000 | 5.0000 |
| M30 | 18640 | 2022-06-02 06:00:00 | 2026-06-01 15:30:00 | 2022-06-02 09:00:00 | 2026-06-01 18:30:00 | 68.0418 | 99.9946 | raw_clock | 997 | 0.0000 | 4.9946 | 5.0000 | 5.0000 |
| M15 | 37276 | 2022-06-02 06:00:00 | 2026-06-01 15:30:00 | 2022-06-02 09:00:00 | 2026-06-01 18:30:00 | 68.0465 | 99.9973 | raw_clock | 998 | 0.0000 | 4.9948 | 5.0000 | 5.0000 |
| M5 | 100000 | 2022-10-26 07:00:00 | 2026-06-01 15:30:00 | 2022-10-26 10:00:00 | 2026-06-01 18:30:00 | 67.9290 | 99.9990 | raw_clock | 898 | 0.0000 | 4.9943 | 5.0000 | 5.0000 |

## Candles por dia

| timeframe | days | min_rows_per_day | median_rows_per_day | max_rows_per_day |
| --- | --- | --- | --- | --- |
| D1 | 997 | 1 | 1.0000 | 1 |
| H1 | 997 | 6 | 10.0000 | 10 |
| H4 | 997 | 2 | 3.0000 | 3 |
| M15 | 997 | 22 | 38.0000 | 39 |
| M30 | 997 | 11 | 19.0000 | 20 |
| M5 | 896 | 65 | 113.0000 | 114 |

## Comparacao raw vs processed

| timeframe | processed_exists | processed_rows | raw_unique_time_rows | row_delta_vs_raw_unique | processed_datetime_column | first_processed_datetime | last_processed_datetime | processed_official_pct | missing_processed_columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | True | 997 | 997 | 0 | datetime_market | 2022-06-02 00:00:00 | 2026-06-01 00:00:00 |  |  |
| H4 | True | 2987 | 2987 | 0 | datetime_market | 2022-06-02 08:00:00 | 2026-06-01 16:00:00 | 66.7559 |  |
| H1 | True | 9683 | 9683 | 0 | datetime_market | 2022-06-02 09:00:00 | 2026-06-01 18:00:00 | 100.0000 |  |
| M30 | True | 18640 | 18640 | 0 | datetime_market | 2022-06-02 09:00:00 | 2026-06-01 18:30:00 | 99.9946 |  |
| M15 | True | 37276 | 37276 | 0 | datetime_market | 2022-06-02 09:00:00 | 2026-06-01 18:30:00 | 99.9973 |  |
| M5 | True | 100000 | 100000 | 0 | datetime_market | 2022-10-26 10:00:00 | 2026-06-01 18:30:00 | 99.9990 |  |

## Proximas acoes recomendadas

1. Usar `datetime_market` como unica coluna temporal canonica nas proximas features, labels e backtests.
2. Manter `time` original e `datetime_utc_to_market` apenas para rastreabilidade/auditoria.
3. Reexecutar este relatorio apos qualquer mudanca no preprocessing ou nos dados.
4. So depois criar features v1 e labels.

## Arquivos gerados

- `reports/data_quality/raw_timeframe_summary.csv`
- `reports/data_quality/daily_counts.csv`
- `reports/data_quality/daily_counts_summary.csv`
- `reports/data_quality/hourly_profile.csv`
- `reports/data_quality/gap_extremes.csv`
- `reports/data_quality/raw_processed_comparison.csv`
- `reports/data_quality/operational_windows.csv`
- `reports/data_quality/data_quality_report.md`
