# Coleta de candles do WIN via MetaTrader 5

Script simples para pegar candles do mini indice pelo MetaTrader 5 ja aberto e logado.

## Timeframes coletados

Por padrao o script busca `10_000` candles de:

- `D1`
- `H4`
- `H1`
- `M30`
- `M15`
- `M5`

O `M1` ficou fora de proposito: para daytrade ele pode ser util depois, mas no comeco tende a trazer ruido e peso demais. O `M5` eu manteria, porque ainda ajuda bastante em entrada, stop, volatilidade intraday e backtest.

## Como usar

Instale a dependencia:

```powershell
pip install -r requirements.txt
```

Abra o MetaTrader 5, faca login, confira o nome do simbolo em `Observacao do Mercado` e ajuste no topo do `main.py`:

```python
SYMBOL = "WINM26"
```

Depois rode:

```powershell
python main.py
```

Os CSVs serao salvos na pasta `data`, um arquivo por timeframe.

Se o simbolo estiver errado, o script lista os simbolos contendo `WIN` disponiveis no seu MT5. Copie exatamente um dos nomes impressos e coloque em `SYMBOL`.

## Observacao importante

Se vierem menos de `10_000` candles, normalmente e limite/historico do proprio MT5 ou da corretora. No MT5, veja:

`Ferramentas > Opcoes > Graficos > Max. barras no grafico`

Para contratos especificos como `WINM26`, o historico tambem pode ser curto por natureza. Para historico maior, muitas corretoras usam simbolos continuos como `WIN$N`.
