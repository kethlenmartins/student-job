# Coleta Glassdoor — versao3

Pipeline em 3 fases para coletar ~5.600 combinações (200 keywords × 28 UFs)
em 2 máquinas com 2 terminais cada.

## Visão geral

```
Fase 1  coleta_glassdoor.py   Cards de todas as buscas (sem descrições)
           ↓  4 terminais em paralelo (~1.3 dias)
Fase 2  deduplicar.py         Remove duplicatas entre buscas
           ↓  1 execução (~15 min)
Fase 3  enriquecer.py         Visita cada vaga única para pegar descrição
           ↓  4 terminais em paralelo (~1.5 dias)
        mesclar.py            Junta os 4 arquivos de saída
```

**Tempo total estimado: ~3 dias**

---

## Setup inicial (fazer uma vez por máquina)

```bash
# 1. Entre na pasta
cd webscrapping-2026/versao3

# 2. Crie o ambiente virtual e instale dependências
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# ou: venv\Scripts\activate   # Windows

pip install -r requirements.txt
playwright install chrome

# 3. Instale tmux se não tiver (para rodar em background)
brew install tmux              # macOS
# ou: sudo apt install tmux    # Linux
```

---

## Fase 1 — Coleta de cards

**Divisão entre terminais:**

| Terminal | Máquina | Keywords | Buscas |
|----------|---------|----------|--------|
| T1       | M1      | 0:50     | 1.400  |
| T2       | M1      | 50:100   | 1.400  |
| T3       | M2      | 100:150  | 1.400  |
| T4       | M2      | 150:200  | 1.400  |

### Primeiro uso — configurar perfis (fazer uma vez)

Cada terminal precisa de um perfil Chrome com login no Glassdoor.
Rode sem `--assume-logged-in`, faça o login quando o Chrome abrir, e pressione Enter.
Depois que o login for confirmado, pode encerrar com Ctrl+C.

```bash
# Máquina 1 — Terminal 1 (perfil t1)
source venv/bin/activate
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 50 --perfil chrome-profile-t1 --sem-enriquecer

# Máquina 1 — Terminal 2 (perfil t2)  ← abrir em outro terminal
source venv/bin/activate
python coleta_glassdoor.py --kw-inicio 50 --kw-fim 100 --perfil chrome-profile-t2 --sem-enriquecer

# Máquina 2 — Terminal 1 (perfil t3)
source venv/bin/activate
python coleta_glassdoor.py --kw-inicio 100 --kw-fim 150 --perfil chrome-profile-t3 --sem-enriquecer

# Máquina 2 — Terminal 2 (perfil t4)  ← abrir em outro terminal
source venv/bin/activate
python coleta_glassdoor.py --kw-inicio 150 --kw-fim 200 --perfil chrome-profile-t4 --sem-enriquecer
```

### Coleta completa com tmux (rodar em background)

Após configurar os perfis, use tmux para deixar rodando desacoplado do terminal.

**Máquina 1:**
```bash
# Terminal 1
tmux new -s t1
source venv/bin/activate
python coleta_glassdoor.py \
  --kw-inicio 0 --kw-fim 50 \
  --perfil chrome-profile-t1 \
  --sem-enriquecer \
  --assume-logged-in
# Ctrl+b d  para desacoplar (processo continua rodando)

# Terminal 2
tmux new -s t2
source venv/bin/activate
python coleta_glassdoor.py \
  --kw-inicio 50 --kw-fim 100 \
  --perfil chrome-profile-t2 \
  --sem-enriquecer \
  --assume-logged-in
# Ctrl+b d  para desacoplar
```

**Máquina 2:**
```bash
# Terminal 1
tmux new -s t3
source venv/bin/activate
python coleta_glassdoor.py \
  --kw-inicio 100 --kw-fim 150 \
  --perfil chrome-profile-t3 \
  --sem-enriquecer \
  --assume-logged-in
# Ctrl+b d  para desacoplar

# Terminal 2
tmux new -s t4
source venv/bin/activate
python coleta_glassdoor.py \
  --kw-inicio 150 --kw-fim 200 \
  --perfil chrome-profile-t4 \
  --sem-enriquecer \
  --assume-logged-in
# Ctrl+b d  para desacoplar
```

**Reconectar para ver o progresso:**
```bash
tmux attach -t t1    # ou t2, t3, t4
```

---

## Fase 2 — Deduplicação

Rodar na **Máquina 1** após ambas as máquinas terminarem a Fase 1.

### 1. Copiar dados da Máquina 2 para a Máquina 1

```bash
# Na Máquina 1, execute:
rsync -av usuario@maquina2:/caminho/versao3/data/bronze/ ./data/bronze/

# Se preferir scp:
scp usuario@maquina2:/caminho/versao3/data/bronze/*.csv ./data/bronze/
```

### 2. Rodar a deduplicação

```bash
# Máquina 1
source venv/bin/activate
python deduplicar.py
```

A saída vai mostrar o total de vagas únicas e os índices exatos para a Fase 3:

```
Vagas únicas: 87.432
  → identificadas por jobListingId: 71.204 (81.4%)
  → identificadas por hash texto:   16.228 (18.6%)

Índices para enriquecer.py:
  Máquina 1, Terminal 1:  --inicio 0       --fim 21858
  Máquina 1, Terminal 2:  --inicio 21858   --fim 43716
  Máquina 2, Terminal 1:  --inicio 43716   --fim 65574
  Máquina 2, Terminal 2:  --inicio 65574   --fim 87432
```

### 3. Copiar vagas_unicas.csv para a Máquina 2

```bash
# Na Máquina 2:
scp usuario@maquina1:/caminho/versao3/data/silver/vagas_unicas.csv ./data/silver/
```

---

## Fase 3 — Enriquecimento

Use os índices exatos que o `deduplicar.py` imprimiu.
Os exemplos abaixo usam 87.432 vagas — **substitua pelos valores reais**.

### Primeiro uso — configurar perfis de enriquecimento

```bash
# Máquina 1 — Terminal 1
source venv/bin/activate
python enriquecer.py --inicio 0 --fim 21858 --perfil chrome-profile-e1

# Máquina 1 — Terminal 2
source venv/bin/activate
python enriquecer.py --inicio 21858 --fim 43716 --perfil chrome-profile-e2

# Máquina 2 — Terminal 1
source venv/bin/activate
python enriquecer.py --inicio 43716 --fim 65574 --perfil chrome-profile-e3

# Máquina 2 — Terminal 2
source venv/bin/activate
python enriquecer.py --inicio 65574 --fim 87432 --perfil chrome-profile-e4
```

### Enriquecimento completo com tmux

**Máquina 1:**
```bash
tmux new -s e1
source venv/bin/activate
python enriquecer.py \
  --inicio 0 --fim 21858 \
  --perfil chrome-profile-e1 \
  --assume-logged-in
# Ctrl+b d

tmux new -s e2
source venv/bin/activate
python enriquecer.py \
  --inicio 21858 --fim 43716 \
  --perfil chrome-profile-e2 \
  --assume-logged-in
# Ctrl+b d
```

**Máquina 2:**
```bash
tmux new -s e3
source venv/bin/activate
python enriquecer.py \
  --inicio 43716 --fim 65574 \
  --perfil chrome-profile-e3 \
  --assume-logged-in
# Ctrl+b d

tmux new -s e4
source venv/bin/activate
python enriquecer.py \
  --inicio 65574 --fim 87432 \
  --perfil chrome-profile-e4 \
  --assume-logged-in
# Ctrl+b d
```

> O script salva um checkpoint a cada 50 vagas. Se cair, basta rodar o mesmo
> comando novamente — ele retoma de onde parou.

---

## Merge final

Após todos os 4 terminais da Fase 3 terminarem:

```bash
# 1. Copiar resultados da Máquina 2 para a Máquina 1
scp usuario@maquina2:/caminho/versao3/data/silver/enriquecido_*.csv ./data/silver/

# 2. Rodar o merge na Máquina 1
source venv/bin/activate
python mesclar.py
```

Arquivo final: `data/silver/vagas_enriquecidas.csv`

---

## Referência rápida dos comandos tmux

| Ação | Comando |
|------|---------|
| Criar sessão nomeada | `tmux new -s nome` |
| Desacoplar (continua rodando) | `Ctrl+b d` |
| Reconectar a uma sessão | `tmux attach -t nome` |
| Listar sessões ativas | `tmux ls` |
| Encerrar sessão | `tmux kill-session -t nome` |

---

## Estrutura de arquivos

```
versao3/
├── coleta_glassdoor.py     Fase 1 — coleta de cards
├── deduplicar.py           Fase 2 — deduplicação cross-busca
├── enriquecer.py           Fase 3 — enriquecimento por URL
├── mesclar.py              Pós-Fase 3 — une os 4 arquivos de saída
├── palavras-chave-vagas.txt
├── requirements.txt
├── README.md
├── chrome-profile-t1/      Perfil Fase 1, M1 T1
├── chrome-profile-t2/      Perfil Fase 1, M1 T2
├── chrome-profile-t3/      Perfil Fase 1, M2 T3  (fica na M2)
├── chrome-profile-t4/      Perfil Fase 1, M2 T4  (fica na M2)
├── chrome-profile-e1/      Perfil Fase 3, M1 T1
├── chrome-profile-e2/      Perfil Fase 3, M1 T2
├── chrome-profile-e3/      Perfil Fase 3, M2 T1  (fica na M2)
├── chrome-profile-e4/      Perfil Fase 3, M2 T2  (fica na M2)
└── data/
    ├── bronze/             CSVs brutos — um por keyword+UF
    ├── silver/
    │   ├── vagas_unicas.csv          Saída do deduplicar.py
    │   ├── enriquecido_0_N.csv       Saída de cada terminal do enriquecer.py
    │   └── vagas_enriquecidas.csv    Saída final do mesclar.py
    └── gold/               (futuro — análises)
```
