# WIN bot

Pipeline inicial para coletar candles do mini indice WIN via MetaTrader 5,
preprocessar os dados e gerar features para modelos tabulares.

## Contexto para Codex

Antes de continuar o projeto em outra sessao do Codex, leia
`README_CODEX.md`. Ele registra o contexto quant, decisoes operacionais,
restricoes de risco, hipoteses de edge e a sequencia correta de proximas fases.

## Instalar dependencias

```powershell
pip install -r requirements.txt
```

## Buscar dados brutos

Abra o MetaTrader 5, faca login, confira o nome do simbolo em
`Observacao do Mercado` e ajuste o topo de `data/fetch_win_data.py` se
necessario:

```python
SYMBOL = "WIN$N"
```

Depois rode:

```powershell
python data\fetch_win_data.py
```

Por padrao, o script busca 4 anos de candles nos timeframes:

- `D1`
- `H4`
- `H1`
- `M30`
- `M15`
- `M5`

Os CSVs brutos sao salvos em `data/raw`, um arquivo por timeframe:
`WIN_D1.csv`, `WIN_H4.csv`, `WIN_H1.csv`, `WIN_M30.csv`, `WIN_M15.csv` e
`WIN_M5.csv`.

## Preprocessar dados

Para ler os CSVs brutos de `data/raw`, normalizar datas e salvar os dados
processados, rode:

```powershell
python preprocessing.py
```

Os CSVs processados sao salvos em `data/processed` com o sufixo
`_processed.csv`.

O preprocessing mantem as colunas brutas do MT5 e adiciona:

- `datetime`
- `datetime_market`
- `datetime_utc_to_market`
- `timeframe`
- `minutes_since_prev`
- `expected_minutes`
- `has_time_gap`
- `is_session_start`
- `gap_points`
- `gap_pct`
- `gap_abs`
- `gap_direction`

`datetime` e `datetime_market` representam o relogio de mercado usado para
features, labels e backtests. `datetime_utc_to_market` existe apenas para
auditoria da interpretacao UTC.

`gap_direction` usa `1` para gap positivo, `-1` para gap negativo e `0` para
sem direcao definida.

## Auditar qualidade dos dados

Antes de criar novas features, labels, modelos ou backtests, rode a auditoria
da Fase 1:

```powershell
python -m win_bot.data_quality
```

Os relatorios sao salvos em `reports/data_quality`:

- `data_quality_report.md`
- `raw_timeframe_summary.csv`
- `daily_counts.csv`
- `daily_counts_summary.csv`
- `hourly_profile.csv`
- `gap_extremes.csv`
- `raw_processed_comparison.csv`
- `operational_windows.csv`

Se `data_quality_report.md` marcar a decisao como `NAO APROVADO PARA
FEATURES/LABELS`, corrija o bloqueio antes de seguir.

## Observacao importante

Se vierem poucos candles, normalmente e limite/historico do proprio MT5 ou da
corretora. No MT5, veja:

`Ferramentas > Opcoes > Graficos > Max. barras no grafico`

Para contratos especificos como `WINM26`, o historico tambem pode ser curto
por natureza. Para historico maior, muitas corretoras usam simbolos continuos
como `WIN$N`.
