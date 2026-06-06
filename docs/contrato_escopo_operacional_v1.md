# Contrato de Escopo Operacional v1

Projeto: `win_bot`

Data: 2026-06-05

Status: aprovado para orientar a Fase 1 depois de revisao do usuario.

Este contrato define as premissas iniciais do projeto antes de criar novas
features, labels, modelos ou backtests. A funcao dele e evitar ambiguidade:
qual ativo estamos estudando, em qual horario, com quais dados, qual evento de
decisao e quais limites operacionais simulados.

## 1. Objetivo da fase

Definir o escopo operacional minimo para pesquisa quantitativa e engenharia de
ML em daytrade de indices, com foco inicial em WIN.

Nesta fase nao ha:

- execucao real de ordens;
- conexao com corretora para operar;
- uso de API keys;
- treinamento de modelos;
- criacao de labels;
- otimizacao de estrategia;
- demo trading.

## 2. Fontes externas usadas como referencia

As premissas abaixo usam a B3 como fonte primaria para especificacao e horarios
do contrato:

- Especificacao do Mini Ibovespa Futures (WIN):
  https://www.b3.com.br/lumis/portal/file/fileDownload.jsp?fileId=8A828D2951C9C37701522260B03227B9
- Horarios de negociacao de derivativos sobre indices:
  https://www.b3.com.br/en_us/products-and-services/trading/equities/cash-equities/trading-dynamics.htm
- Circular B3 005/2026-PRE sobre horarios:
  https://www.b3.com.br/data/files/54/23/16/15/EC09C910F37907C9AC094EA8/OC%20005-2026%20PRE%20NOVOS%20HORARIOS%20DE%20NEGOCIACAO_ING.pdf

Observacao: horarios, regras de vencimento e parametros de mercado podem mudar.
Antes de qualquer fase demo ou real, este contrato deve ser revalidado.

## 3. Ativo e simbolo

Ativo de pesquisa inicial:

- `WIN$N` no MetaTrader 5.

Motivo:

- permite trabalhar com uma serie continua maior no ambiente atual;
- reduz o problema pratico de baixar cada contrato individualmente no inicio;
- ja existe dado bruto coletado para esse simbolo.

Risco:

- a regra de continuidade de `WIN$N` depende da corretora/servidor MT5;
- rolagem pode criar saltos, retornos artificiais ou gaps que nao seriam
  exatamente iguais aos de um contrato especifico;
- qualquer conclusao deve tratar `WIN$N` como fonte de pesquisa, nao como
  instrumento direto de execucao.

Ativo de execucao futura:

- contrato vigente especifico, por exemplo `WINM26`, apenas em fase demo/real.

## 4. Especificacao operacional do WIN

Premissas iniciais:

- ticker B3: `WIN`;
- valor do ponto: R$ 0,20 por contrato;
- tick minimo: 5 pontos;
- meses de vencimento: meses pares, podendo haver autorizacao de meses impares;
- vencimento: quarta-feira mais proxima do dia 15 do mes de vencimento;
- horario regular de referencia: 09:00 ate 18:25;
- pre-abertura: 5 minutos antes da fase de negociacao;
- contrato em vencimento pode ter regra especial de encerramento;
- janela de apuracao de preco de ajuste do WIN/IND: 17:00 ate 17:15, conforme
  referencia da B3.

Implicacao tecnica:

- backtests nao devem operar cegamente perto de vencimento;
- features de sessao devem respeitar horario de Sao Paulo;
- fechamento, ajuste e vencimento devem ser tratados como regimes especiais;
- o relatorio de qualidade deve comparar os candles reais com essas premissas.

## 5. Timezone e calendario

Timezone padrao de pesquisa:

- `America/Sao_Paulo`.

Timestamp original:

- manter a coluna `time` Unix original do MT5 para rastreabilidade.

Decisao v1 sobre a base temporal:

- nao alterar os CSVs brutos em `data/raw`;
- manter a coluna `time` original do MT5 para rastreabilidade;
- nos dados processados, `datetime_market` sera o horario canonico de mercado;
- a coluna `datetime` sera mantida como alias de `datetime_market` por
  compatibilidade;
- `datetime_utc_to_market` sera mantida apenas como coluna de auditoria;
- features de sessao, filtros de horario, labels e backtests devem usar
  `datetime_market`.

Motivo:

- features como hora, abertura, fechamento, lunch effect, volatilidade por
  sessao e janela de eventos dependem de timezone correto;
- misturar UTC, horario da corretora e horario local cria data leakage
  operacional e interpretacao errada de sessao.
- corrigir a base temporal nos processados agora reduz o risco de bugs
  silenciosos nas proximas fases.

Validacao obrigatoria na Fase 1:

- conferir primeiro e ultimo candle por timeframe;
- conferir se candles intraday caem dentro de horarios plausiveis;
- marcar candles fora da janela esperada;
- validar comportamento de D1, pois candle diario pode aparecer com horario
  diferente do intuitivo apos conversao de timezone.
- medir a diferenca entre `datetime_market` e `datetime_utc_to_market` apenas
  para auditoria.

## 6. Timeframes

Timeframes brutos mantidos:

- `D1`;
- `H4`;
- `H1`;
- `M30`;
- `M15`;
- `M5`.

Papel inicial de cada grupo:

- `D1`, `H4`, `H1`: contexto e regime, nunca gatilho direto inicial;
- `M30`, `M15`: decisao direcional inicial;
- `M5`: execucao simulada e resolucao mais fina de alvo/stop.

Decisao v1:

- timeframe principal de decisao: `M15`;
- timeframe principal de execucao/backtest: `M5`;
- `M1` fica fora da primeira versao.

Motivo:

- `M15` reduz ruido e overtrading em relacao ao `M5`;
- `M5` melhora a simulacao de stop/alvo em relacao ao `M15`;
- `M1` aumenta peso, ruido e risco de microestrutura mal modelada no inicio.

## 7. Janela operacional simulada

Horario oficial observado para FUT WIN:

- 09:00 ate 18:25.

Janela de decisao inicial recomendada:

- 10:00 ate 16:30.

Zeragem simulada inicial:

- ate 17:00.

Janela de abertura:

- 09:00 ate 10:00 sera bloqueada para trades na v1;
- essa primeira hora sera usada apenas para medir o regime do dia, volatilidade,
  gap, spread, range inicial, direcao inicial e volume relativo.

Motivo:

- evitar a primeira hora de abertura ate medir spread, volatilidade,
  comportamento de gaps, absorcao de fluxo overnight e formacao do range
  inicial;
- evitar fechamento, ajuste e regioes com dinamica operacional diferente;
- manter a primeira versao conservadora e facil de auditar.

Validacao na Fase 1:

- medir candles por horario;
- medir spread medio/p95/maximo por horario;
- medir volume e gaps por horario;
- decidir se 10:00 e 16:30 sao janelas adequadas ou conservadoras demais;
- testar posteriormente, em experimento separado, janelas alternativas como
  09:30+, 09:45+ e 10:00+.
- validar que os filtros futuros usam `datetime_market`, nao a coluna de
  auditoria `datetime_utc_to_market`.

## 8. Premissas de custo e slippage

Valor financeiro do contrato:

- 1 ponto do WIN por contrato = R$ 0,20;
- tick minimo = 5 pontos = R$ 1,00 por contrato.

Custos fixos v1 para pesquisa:

- corretagem de entrada: R$ 0,00 por contrato;
- corretagem de saida: R$ 0,00 por contrato;
- custo fixo estimado B3/corretora/taxas por round trip: R$ 2,00 por contrato
  no cenario principal de aprovacao;
- zeragem compulsoria: nao deve ocorrer no backtest normal; se ocorrer por erro
  operacional em simulacao/demo, usar penalidade de R$ 16,00 por contrato;
- custos de plataforma/robo: R$ 0,00 na pesquisa local; para stress
  operacional, considerar R$ 1,50 por contrato quando houver infraestrutura que
  cobre por contrato.

Slippage inicial para pesquisa:

- cenario otimista controlado: 5 pontos por lado;
- cenario base: 10 pontos por lado;
- cenario principal de aprovacao: 20 pontos por lado.

Spread:

- usar a coluna `spread` como dado observado, depois de validar sua qualidade.

Motivo:

- assumir execucao perfeita cria backtest irrealista;
- custo exato depende de corretora, taxa, liquidez, roteamento e horario;
- a estrategia precisa sobreviver ao pior cenario de custo antes de demo/real.

Modelo de custo por trade:

```text
pnl_bruto_reais =
    pontos_liquidos_do_trade * 0.20 * contratos

custo_slippage_reais =
    (slippage_entrada_pontos + slippage_saida_pontos) * 0.20 * contratos

pnl_liquido_reais =
    pnl_bruto_reais
    - custo_fixo_round_trip_reais
    - custo_slippage_reais
```

Cenarios iniciais para 1 contrato:

| Cenario | Custo fixo round trip | Slippage | Custo total aproximado |
| --- | ---: | ---: | ---: |
| Diagnostico otimista | R$ 1,00 | 5 pts/lado = R$ 2,00 | R$ 3,00 |
| Diagnostico base | R$ 1,00 | 10 pts/lado = R$ 4,00 | R$ 5,00 |
| Principal de aprovacao | R$ 2,00 | 20 pts/lado = R$ 8,00 | R$ 10,00 |

Em pontos equivalentes por contrato:

- R$ 3,00 = 15 pontos;
- R$ 5,00 = 25 pontos;
- R$ 10,00 = 50 pontos.

Regra de aprovacao:

- o cenario `Principal de aprovacao` sera o padrao para decidir se uma
  estrategia/modelo passa ou nao;
- os cenarios `Diagnostico otimista` e `Diagnostico base` servem apenas para
  analise de sensibilidade;
- uma estrategia que so funciona nos cenarios menores sera considerada
  reprovada para demo/real.

Stress operacional adicional:

| Cenario | Componente extra | Custo total aproximado | Pontos equivalentes |
| --- | ---: | ---: | ---: |
| Principal + robo/plataforma | R$ 1,50 | R$ 11,50 | 57,5 pontos |
| Principal + zeragem compulsoria | R$ 16,00 | R$ 26,00 | 130 pontos |
| Principal + robo + zeragem compulsoria | R$ 17,50 | R$ 27,50 | 137,5 pontos |

Observacao:

- zeragem compulsoria nao representa um trade normal; representa falha
  operacional ou descumprimento de zeragem propria do bot;
- qualquer ocorrencia de zeragem compulsoria em demo deve acionar revisao do
  motor operacional antes de pensar em real;
- para comparacoes em pontos, arredondar custos para cima em multiplos de 5
  pontos quando isso for usado como barreira minima.

Referencia operacional atual observada:

- a pagina de custos da Clear informa corretagem R$ 0,00 e margem day trade de
  Mini Indice (WIN), mas emolumentos e taxas seguem referencias da B3/CBLC;
- a mesma pagina informa custo de zeragem compulsoria para WIN e custo
  especifico para robos/estrategias automatizadas Ontick quando aplicavel;
- por isso, o backtest deve manter custos como parametros e rodar stress de
  custo, nao depender de um unico numero fixo.

## 9. Restricoes de risco simuladas

Versao inicial de pesquisa:

- intraday apenas;
- sem overnight;
- 1 contrato como unidade de simulacao;
- sem aumento automatico de mao;
- sem martingale;
- sem pyramiding na primeira versao;
- limite de trades por dia sera definido apenas apos baseline;
- stop diario sera definido antes de qualquer demo.

Prioridade operacional absoluta:

- nunca manter trade aberto depois de qualquer gatilho de saida;
- gatilho de alvo deve encerrar a posicao;
- gatilho de stop deve encerrar a posicao;
- gatilho de horario deve encerrar a posicao;
- gatilho de kill switch ou stop diario deve encerrar a posicao e bloquear
  novas entradas;
- se houver conflito entre manter posicao e zerar por seguranca, a regra de
  zeragem vence sempre.

Motivo:

- simplifica validacao;
- evita transformar uma estrategia ruim em uma estrategia aparentemente boa por
  aumento de risco;
- separa edge estatistico de alavancagem.
- trata falha de saida como risco operacional critico, nao como variacao normal
  de resultado.

Regra de falha critica:

- qualquer trade que permaneca aberto depois de alvo, stop, horario limite,
  kill switch ou stop diario sera marcado como erro operacional;
- em shadow/demo, uma unica ocorrencia desse tipo bloqueia avanco para real ate
  o motor de execucao ser corrigido e retestado;
- no backtest, esse caso deve ser impossivel por construcao. Se aparecer, o
  backtest esta errado.

## 10. Regras contra data leakage

Regras obrigatorias:

- qualquer feature precisa estar conhecida no instante de decisao;
- candle usado para gerar feature precisa estar fechado;
- candle maior (`H1`, `H4`, `D1`) so pode entrar se ja estiver fechado ou se a
  feature for explicitamente tratada como parcial;
- normalizacao, scaler, selecao de features e calibracao devem ser fitados
  apenas no treino de cada janela walk-forward;
- colunas de label/diagnostico como retorno futuro, MFE, MAE, motivo de saida
  e `label_end_time` nunca entram no feature set;
- entrada simulada nao pode ocorrer no mesmo fechamento que gerou o sinal.
- horarios de pregao, abertura, bloqueio, decisao e zeragem devem ser aplicados
  sobre `datetime_market`.

## 11. Definicao inicial de evento

Evento de decisao v1:

- ocorre no fechamento de um candle `M15` elegivel.

Entrada simulada v1:

- ocorre no proximo candle disponivel, preferencialmente resolvida em `M5`.

Horizonte e barreiras:

- ainda nao definidos nesta fase;
- serao definidos na fase de labels, depois do relatorio de qualidade e das
  features v1.

Motivo:

- primeiro precisamos garantir que dados, horarios e gaps sao confiaveis;
- definir labels antes da qualidade dos dados aumenta risco de medir sujeira.

## 12. O que a Fase 1 deve validar

A Fase 1 sera o Data Quality Report v1.

Ela deve responder:

- os CSVs brutos tem schema correto?
- quais sao os periodos disponiveis por timeframe?
- existe intersecao temporal suficiente entre `M15` e `M5`?
- existem duplicatas?
- quantos candles existem por dia e por horario?
- os gaps observados parecem normais ou ha buracos suspeitos?
- `real_volume` e confiavel ou vem zerado/inconsistente?
- `spread` e confiavel para filtro e custo?
- existem candles fora do horario esperado?
- a conversao para `America/Sao_Paulo` esta coerente?
- o uso de `WIN$N` cria saltos anormais em rolagens?

## 13. Criterios de conclusao da Fase 0

A Fase 0 esta concluida quando:

- este contrato esta salvo no repositorio;
- o usuario revisou e aceitou as premissas v1;
- as decisoes abertas foram marcadas para validacao na Fase 1;
- nenhuma implementacao de modelo, label ou execucao real foi feita.

## 14. Decisoes abertas

As decisoes abaixo nao devem ser resolvidas por chute:

- custo total por trade;
- stop diario;
- limite maximo de trades por dia;
- regra final de vencimento/rolagem;
- uso ou descarte de `real_volume`;
- janela operacional definitiva;
- barreiras do triple barrier;
- criterios de passagem para shadow/demo.

Esses itens dependem dos resultados da Fase 1 e das fases posteriores.
