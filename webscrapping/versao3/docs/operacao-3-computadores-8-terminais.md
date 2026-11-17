# Operação distribuída: 3 computadores e 8 terminais

Este guia executa uma rodada nova do pipeline sem sobrepor arquivos entre
terminais. A distribuição é:

| Computador | Terminais | Total |
| --- | --- | ---: |
| PC 1 | T1, T2, T3 | 3 |
| PC 2 | T1, T2, T3 | 3 |
| PC 3 | T1, T2 | 2 |
| **Total** |  | **8** |

Todos os computadores devem ter a mesma versão do repositório, dependências
instaladas, Chrome e uma cópia de `criterios-2026.xlsx`. Cada terminal precisa
usar um perfil Chrome próprio; nunca reutilize o mesmo perfil em dois processos.

Neste exemplo, a rodada chama-se `2026-nova`. Substitua esse valor por um
identificador novo e mantenha-o idêntico em todos os comandos.

## Preparação no Windows

Faça esta preparação **uma vez em cada computador**, no PowerShell. São
necessários Python 3.10 ou superior, Git e Google Chrome instalados.

```powershell
cd $HOME\student-job
git pull origin main
cd webscrapping\versao3

py -3 -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chrome
```

`Set-ExecutionPolicy` vale somente para aquela janela do PowerShell e permite
ativar o ambiente virtual sem alterar a política permanente do computador.
Se `py -3` não existir, instale o Python pelo instalador oficial e marque a
opção para adicioná-lo ao PATH; depois, substitua `py -3` por `python`.

Abra uma janela PowerShell por terminal planejado. Em **cada janela**, entre
na pasta do projeto e ative o mesmo ambiente antes de rodar qualquer comando:

```powershell
cd $HOME\student-job\webscrapping\versao3
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Se a ativação por PowerShell não for permitida, use o Prompt de Comando (CMD):

```bat
cd %USERPROFILE%\student-job\webscrapping\versao3
venv\Scripts\activate.bat
```

Nos comandos de coleta e enriquecimento abaixo, os argumentos são iguais no
Windows. No PowerShell, use a crase (acento grave) no fim da linha para
quebrar um comando em várias linhas, ou execute-o todo em uma única linha.

## 1. Coleta Bronze

Há 200 palavras-chave. Divida-as em oito faixas de 25, sempre pesquisando todas
as UFs. Rode um comando por terminal e aguarde todos terminarem.

| Terminal | Faixa `--kw-inicio:--kw-fim` | Perfil |
| --- | --- | --- |
| PC 1 · T1 | `0:25` | `chrome-profile-coleta-pc1-t1` |
| PC 1 · T2 | `25:50` | `chrome-profile-coleta-pc1-t2` |
| PC 1 · T3 | `50:75` | `chrome-profile-coleta-pc1-t3` |
| PC 2 · T1 | `75:100` | `chrome-profile-coleta-pc2-t1` |
| PC 2 · T2 | `100:125` | `chrome-profile-coleta-pc2-t2` |
| PC 2 · T3 | `125:150` | `chrome-profile-coleta-pc2-t3` |
| PC 3 · T1 | `150:175` | `chrome-profile-coleta-pc3-t1` |
| PC 3 · T2 | `175:200` | `chrome-profile-coleta-pc3-t2` |

Modelo do comando (ajuste somente a faixa e o perfil conforme a tabela):

```bash
cd webscrapping/versao3
python coleta_glassdoor.py \
  --run-id 2026-nova \
  --kw-inicio 0 --kw-fim 25 \
  --perfil chrome-profile-coleta-pc1-t1 \
  --sem-enriquecer \
  --max-vagas-por-busca 300 --max-pausa 10
```

Na primeira execução de cada perfil, faça login manualmente. Nas retomadas, se
a sessão ainda estiver ativa, acrescente `--assume-logged-in`. O script retoma
as buscas cujo CSV Bronze ainda não existe; não apague arquivos já concluídos.

## 2. Unificar Bronze, deduplicar e criar a fila tech

Escolha o PC 1 como coordenador. Depois que os oito terminais terminarem,
copie para ele os CSVs de Bronze dos PCs 2 e 3, preservando a pasta da rodada:

```text
data/runs/2026-nova/bronze/
```

Não copie ou compartilhe perfis Chrome. Confirme que há 5.400 CSVs esperados
(200 palavras-chave × 27 UFs; resultados vazios também geram CSV) antes de
prosseguir. No PC 1, execute:

```bash
cd webscrapping/versao3
python deduplicar.py --run-id 2026-nova
python filtrar_tech.py \
  --input-file data/runs/2026-nova/silver/vagas_unicas.csv
```

Copie a pasta `data/runs/2026-nova/silver/` resultante para os PCs 2 e 3. Ela
contém a mesma `fila_tech.csv` que será particionada no passo seguinte.

## 3. Enriquecimento em oito fatias

Cada terminal executa um intervalo exclusivo da `fila_tech.csv`. Primeiro,
conte as linhas no PC 1 (o resultado é o valor `TOTAL`):

```bash
python3 -c "import csv; print(sum(1 for _ in csv.DictReader(open('data/runs/2026-nova/silver/fila_tech.csv', encoding='utf-8'))))"
```

Calcule os limites `B0` a `B8` com `Bi = floor(TOTAL × i / 8)`. Distribua os
intervalos assim:

| Terminal | Intervalo |
| --- | --- |
| PC 1 · T1 | `B0:B1` |
| PC 1 · T2 | `B1:B2` |
| PC 1 · T3 | `B2:B3` |
| PC 2 · T1 | `B3:B4` |
| PC 2 · T2 | `B4:B5` |
| PC 2 · T3 | `B5:B6` |
| PC 3 · T1 | `B6:B7` |
| PC 3 · T2 | `B7:B8` |

Por exemplo, para o volume histórico de 15.514 vagas, as fatias são:
`0:1939`, `1939:3878`, `3878:5817`, `5817:7757`, `7757:9696`,
`9696:11635`, `11635:13574` e `13574:15514`.

Use dois workers (abas) por terminal no início: são 16 abas no total. Se a
taxa de erro ou captcha subir, reduza para um worker por terminal antes de
tentar aumentar a concorrência.

```bash
cd webscrapping/versao3
python enriquecer_paralelo.py \
  --input-file data/runs/2026-nova/silver/fila_tech.csv \
  --inicio 0 --fim 1939 \
  --perfil chrome-profile-enrich-pc1-t1 \
  --workers 2 --assume-logged-in
```

Na primeira vez de cada perfil, remova `--assume-logged-in`, faça o login e só
então use a opção nas retomadas. Cada terminal grava um arquivo incremental
`enriquecido_paralelo_*.csv`; interromper e repetir o mesmo comando retoma as
linhas já concluídas.

## 4. Consolidar os resultados

Quando todas as oito fatias terminarem, copie os oito arquivos
`enriquecido_paralelo_*.csv` para a pasta abaixo no PC 1:

```text
data/runs/2026-nova/silver/
```

No coordenador, confira que há oito arquivos de saída com intervalos distintos
e execute:

```bash
cd webscrapping/versao3
python mesclar.py --run-id 2026-nova
```

O resultado será `data/runs/2026-nova/silver/vagas_enriquecidas.csv`.
Não misture arquivos de `enriquecer.py` (legado) com os arquivos
`enriquecer_paralelo.py` para a mesma fatia.
