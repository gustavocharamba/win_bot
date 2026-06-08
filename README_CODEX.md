# Codex Context

Leia este arquivo antes de alterar o projeto. Ele resume as decisoes de
pesquisa, escopo operacional e proximos passos para que outra sessao do Codex
continue o trabalho sem perder o contexto.

## Postura do projeto

Este e um projeto serio de pesquisa quantitativa e engenharia de ML para
daytrade no mini indice WIN. O papel esperado do Codex e agir como um quant
researcher + ML engineer senior, com foco em:

- series temporais financeiras;
- validacao temporal;
- backtest realista;
- prevencao de data leakage e look-ahead bias;
- custo, slippage, risco e execucao operacional;
- rejeitar ideias que so funcionam em backtest fragil.

Nada deve ser implementado porque "parece bom". Cada etapa precisa ter
hipotese, motivo tecnico, validacao e criterio de parada.

## Escopo atual

Foco atual: daytrade operacional no WIN.

Fora do escopo inicial:

- convergence/statistical arbitrage;
- execucao real de ordens;
- API keys;
- conexao com exchange/corretora para operar;
- deep learning;
- LLM/noticias como sinal direcional;
- aumento de mao, martingale, pyramiding ou recuperacao de loss.

Relative value/stat arb foi discutido, mas ficou como tese futura. A decisao
atual e focar em WIN por ser mais simples operacionalmente para capital pequeno.

## Capital e operacao futura

Capital de referencia discutido: R$ 10.000.

Interpretacao correta: esse capital nao e meta de renda. Ele serve como
referencia de sobrevivencia operacional para uma eventual fase real minima.

Regras futuras iniciais:

- real minimo somente com 1 contrato;
- nunca aumentar mao para recuperar perda;
- stop diario obrigatorio antes de demo;
- stop semanal/mensal antes de real;
- zeragem obrigatoria por alvo, stop, horario, kill switch ou stop diario;
- qualquer falha de zeragem bloqueia avanco para real.

## Documentos principais

- `docs/plano_quant_revisado_daytrade_win_ml.pdf`
  - Plano v2.1 operacional.
  - Foco definitivo em daytrade no WIN.
  - Data Quality Report v1 aprovado para features/labels.
  - Pontos observados viram controles de pesquisa, nao bloqueios.

- `docs/contrato_escopo_operacional_v1.md`
  - Contrato operacional base.
  - Define ativo, horarios, custos, janela de trade, timezone, riscos e regras
    contra leakage.

- `reports/data_quality/data_quality_report.md`
  - Relatorio da Fase 1.
  - Atualmente aprovado para features/labels.

## Estado atual dos dados

Dados brutos:

- pasta: `data/raw`;
- simbolo: `WIN$N`;
- timeframes: `D1`, `H4`, `H1`, `M30`, `M15`, `M5`.

Dados processados:

- pasta: `data/processed`;
- gerados por `python preprocessing.py`;
- ignorados pelo git via `.gitignore`.

Colunas temporais importantes:

- `time`: timestamp Unix original do MT5, mantido para rastreabilidade;
- `datetime_market`: relogio canonico de mercado;
- `datetime`: alias de `datetime_market`;
- `datetime_utc_to_market`: somente auditoria.

Regra: features, labels, filtros de sessao e backtests devem usar
`datetime_market`.

## Controles de pesquisa dos dados

O dataset esta aprovado para features/labels, mas os pontos abaixo precisam ser
controlados:

- `M5` comeca em `2022-10-26`, depois dos timeframes maiores;
- labels/backtests que dependem de `M5` devem usar a intersecao comum
  `M15`/`M5`;
- `spread` esta praticamente constante em 5, entao nao usar como unico proxy de
  custo dinamico sem validacao adicional;
- `WIN$N` e uma serie continua da corretora/servidor MT5, logo rolagens devem
  ser auditadas;
- `H4` comeca como review e nao deve entrar automaticamente sem regra clara de
  candle fechado;
- calendario B3/feriados/pregoes encurtados ainda deve virar controle
  explicito antes de features finais de sessao.

## Hipoteses de edge v1

Nao criar feature zoo. Toda feature deve estar ligada a uma hipotese.

Hipoteses iniciais:

1. No-trade gate
   - Pergunta: quando o mercado esta ruim demais para operar?
   - Objetivo: reduzir overtrading e drawdown.

2. Continuacao direcional apos pullback
   - Pergunta: em contexto direcional, pullbacks controlados tendem a
     continuar?
   - Possiveis contextos: VWAP, tendencia H1/M15, ATR, high/low so far,
     volume relativo.

3. Rompimento aceito vs falso rompimento
   - Pergunta: quando rompe maxima/minima relevante, o preco aceita a nova
     regiao ou falha?
   - Niveis candidatos: maxima/minima da primeira hora, maxima/minima do dia,
     fechamento anterior, VWAP.

4. Exaustao / veto de entrada atrasada
   - Pergunta: quando o movimento ja esta esticado demais para entrar a favor?
   - Usar primeiro como filtro de veto, nao como estrategia reversiva
     agressiva.

5. Risco de sessao/evento
   - Pergunta: quais horarios ou condicoes destroem expectativa?
   - Janelas ruins devem virar bloqueio operacional.

## Arquitetura de modelos

Nao existe um modelo por feature.

Feature e insumo. Modelo e decisor.

Arquitetura correta:

```text
dados processados
-> filtros duros
-> no-trade gate
-> setup/sinal
-> meta-label accept/reject
-> risco/tamanho
-> execucao/backtest
-> logs
```

Modelos separados so fazem sentido por hipotese de edge ou etapa de decisao,
nunca por indicador isolado.

Exemplo correto:

```text
features de tempo + volatilidade + VWAP + range inicial + contexto H1
-> no-trade gate ou modelo de continuacao

features de rompimento + aceitacao + volume + distancia da VWAP
-> modelo/filtro de rompimento aceito vs falso rompimento
```

Exemplo errado:

```text
um modelo para RSI
um modelo para ATR
um modelo para volume
um modelo para gap
```

Isso fragmenta o sinal, aumenta overfitting e dificulta auditoria.

## Sequencia correta daqui para frente

Proxima fase nao e ML.

Sequencia recomendada:

1. Alinhar o codigo/relatorio para manter decisao aprovada.
2. Criar data freeze com hashes e periodo comum M15/M5.
3. Criar registro das hipoteses de edge v1.
4. Rodar event studies sem ML.
5. Selecionar features v1 ligadas as hipoteses aprovadas.
6. Formalizar evento de decisao e entrada.
7. Implementar labels triple barrier.
8. Medir baselines sem ML.
9. Treinar modelo tabular simples com walk-forward.
10. Rodar backtest conservador com stress de custo.
11. Shadow mode.
12. Demo com 1 contrato.
13. Real minimo apenas se demo e backtest forem consistentes.

## Comandos importantes

O Python do sistema pode nao estar no PATH e a `.venv` local pode estar
quebrada. Se necessario, usar o Python embutido do Codex:

```powershell
C:\Users\gusta\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

Preprocessar:

```powershell
python preprocessing.py
```

Auditar dados:

```powershell
python -m win_bot.data_quality
```

Compilar pacote:

```powershell
python -m compileall win_bot
```

## Regras de seguranca para qualquer Codex futuro

- Nao conectar em corretora para operar.
- Nao criar API keys.
- Nao enviar ordem real.
- Nao implementar bot inteiro de uma vez.
- Nao treinar ML antes de event studies e baselines.
- Nao usar split aleatorio para medir performance financeira.
- Nao usar candle maior em formacao como se estivesse fechado.
- Nao colocar MFE, MAE, retorno futuro ou label_end_time no feature set.
- Nao otimizar hiperparametros antes de definir metricas e walk-forward.
- Nao aumentar complexidade sem motivo tecnico.
- Se algo parecer fraco, diga claramente.

## Estado git esperado

No momento em que este arquivo foi criado, havia mudanca pendente no PDF:

- `docs/plano_quant_revisado_daytrade_win_ml.pdf`

Este arquivo tambem deve aparecer como novo/alterado ate ser commitado.

