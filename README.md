## Timeframes coletados via MT5

Por padrao o script busca 4 anos:

- `1D`
- `4H`
- `1H`
- `30M`
- `15M`
- `5M`

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
