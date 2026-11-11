# Plano de evolução: coleta 2026 em máquina única

## Objetivo

Reduzir a coleta cara de descrições no Glassdoor e eliminar o uso de vários
processos Chrome. A nova ordem do pipeline classifica a vaga pelo título antes
do enriquecimento e visita somente as vagas que podem pertencer ao recorte
tech.

## Contexto e evidência

Na rodada anterior, o pipeline produziu aproximadamente:

| Camada | Volume aproximado |
| --- | ---: |
| Bronze, cards coletados | 800 mil |
| Silver, após deduplicação e filtros | 160 mil |
| Gold, vagas tech | 15 mil |

O notebook `analytics/scp_01.ipynb` seleciona vagas tech apenas a partir de
`Funcao` (renomeada para `Cargo`). Ele normaliza o título e procura qualquer
termo da aba `palavras_chave` da planilha de critérios. A descrição/coluna
`Skills Necessarias` não participa dessa decisão. Portanto, aplicar a mesma
regra antes de abrir a página individual da vaga preserva o critério histórico
e evita enriquecer a maior parte das vagas Silver.

## Pipeline proposto

```text
coleta de cards
  → Bronze
  → deduplicação
  → Silver: vagas_unicas.csv
  → triagem por título
      ├─ fila_tech.csv       → enriquecimento concorrente
      ├─ fila_ambigua.csv    → segunda fila, se necessária
      └─ fila_nao_tech.csv   → arquivamento com justificativa
  → merge do enriquecimento
  → Gold e notebooks analíticos
```

## Regra de triagem

### Fonte dos critérios

- Termos tech: aba `palavras_chave`, coluna `Cargo`, de `criterios-2026.xlsx`.
- Termos de exclusão: aba `blacklist`, coluna `Termo`, da mesma planilha.
- Texto classificado: coluna `Funcao` de `vagas_unicas.csv`.

### Normalização

Aplicar exatamente a preparação usada em `scp_01.ipynb`: remover acentos,
converter para minúsculas e padronizar separadores (`/`, `|`, `.`, parênteses,
colchetes, `:` e hífen). Os termos e o título devem ser delimitados para evitar
que uma palavra curta corresponda a parte de outra palavra.

### Classes

| Classe | Condição | Ação |
| --- | --- | --- |
| `tech` | Pelo menos um termo tech e nenhum termo da blacklist | Enriquecer nesta rodada |
| `ambigua` | Pelo menos um termo tech e pelo menos um termo da blacklist | Guardar em fila separada; enriquecer ou revisar por amostragem antes de excluir |
| `nao_tech` | Nenhum termo tech | Não enriquecer; preservar o registro e o motivo |

`Prioridade` da planilha não será interpretada como confiança: no critério
atual ela ordena termos, mas contém tanto termos específicos como genéricos em
valores diferentes. A regra de inclusão permanece “qualquer termo tech”, como
no `scp_01`.

## Arquivos gerados pela triagem

O script `filtrar_tech.py` gera na pasta Silver da rodada:

- `fila_tech.csv`
- `fila_ambigua.csv`
- `fila_nao_tech.csv`
- `relatorio_triagem.json`

Cada CSV deve manter as colunas originais e acrescentar:

- `classe_triagem`
- `termos_tech_encontrados`
- `termos_blacklist_encontrados`
- `versao_criterios`: hash SHA-256 da planilha usada
- `source_index`: índice estável da linha no Silver de origem

Esses campos tornam a decisão reproduzível, auditável e reversível sem uma
nova coleta Bronze.

## Enriquecimento em uma máquina

Usar `enriquecer_paralelo.py` sobre `fila_tech.csv`, depois opcionalmente sobre
`fila_ambigua.csv`.

- Manter um único processo Chrome persistente, com perfil exclusivo.
- Iniciar com quatro abas (`--workers 4`) e observar timeout, login e páginas
  sem descrição; só aumentar a concorrência se a taxa de falha permanecer
  estável.
- Manter a fila limitada, persistência por linha e retomada no mesmo arquivo de
  saída.
- Usar um watchdog por vaga: ao exceder o timeout total, registrar o erro;
  após falhas consecutivas, recriar a aba. Se o contexto Chrome não responder,
  reiniciar automaticamente o processo e retomar a partir do CSV incremental.
  Os parâmetros operacionais são `--timeout-item` (60 segundos por padrão) e
  `--max-auto-restarts` (8 por padrão). A retomada automática recoloca na fila
  apenas as linhas que haviam terminado com erro.
- Pausar/reduzir a concorrência diante de bloqueio ou aumento persistente de
  falhas. Mais containers não aumentam a capacidade do Glassdoor para o mesmo
  IP/conta e multiplicam uso de RAM e locks de perfil.

Containers podem ser usados posteriormente para isolar tarefas locais de CPU
(triagem, validação e análises), mas não são a unidade de paralelismo indicada
para o navegador autenticado.

## Implementação em etapas

1. Criar a rodada isolada com `--run-id` na coleta Bronze.
2. Rodar `filtrar_tech.py` e gerar as três filas com os motivos.
3. Usar `enriquecer_paralelo.py --input-file fila_tech.csv`, sem alterar o
   Silver original.
4. Rodar a triagem sobre uma cópia do Silver histórico e comparar a fila
   `tech` com a saída do `scp_01`.
5. Auditar uma amostra dos casos `ambigua` e `nao_tech`; ajustar somente a
   planilha de critérios, mantendo o código estável.
6. Executar a nova coleta com enriquecimento apenas da fila tech e consolidar
   os resultados no Gold.

## Comandos da rodada

Substitua `2026-10` pelo identificador da rodada e inicie a primeira execução
de cada perfil sem `--assume-logged-in`, para validar a sessão.

```bash
# Bronze (piloto: uma keyword e duas UFs; aumente a fatia depois de validar)
python coleta_glassdoor.py --run-id 2026-10 --kw-inicio 0 --kw-fim 1 \
  --ufs SP,RJ --perfil chrome-profile-t3 --sem-enriquecer

# Silver e triagem
python deduplicar.py --run-id 2026-10
python filtrar_tech.py \
  --input-file data/runs/2026-10/silver/vagas_unicas.csv

# Enriquecimento somente da fila tech
python enriquecer_paralelo.py \
  --input-file data/runs/2026-10/silver/fila_tech.csv \
  --perfil chrome-profile-e5 --workers 4 --assume-logged-in

# Consolidação
python mesclar.py --run-id 2026-10
```

## Critérios de aceite

- A fila `tech` reproduz o conjunto do `scp_01` para uma base histórica fixa,
  salvo exclusões deliberadas e documentadas pela blacklist.
- Cada linha possui classe e termos que justificam a classificação.
- Uma interrupção não perde resultados já enriquecidos nem repete páginas
  concluídas.
- O processo opera com um Chrome e concorrência limitada, sem locks de perfil
  ou crescimento de memória proporcional ao tamanho total do CSV.
- O relatório informa totais por classe, taxa de descrição encontrada, erros,
  tempo por vaga e versão dos critérios.
