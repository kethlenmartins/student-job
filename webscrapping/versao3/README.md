# Coleta de Vagas Glassdoor 2026 — Guia de Participação

Obrigada por ajudar! Este documento explica tudo que você precisa fazer na sua
máquina para a coleta funcionar. Você não precisa ler o guia todo — só a seção
com o seu nome.

---

## O que é este projeto?

Estamos coletando dados de vagas de emprego em tecnologia do Glassdoor Brasil
para uma pesquisa de carreiras. O objetivo é entender quais habilidades,
salários e regiões aparecem mais nas vagas de tech — tudo automatizado.

Como o volume é grande (~5.400 buscas no total), dividimos o trabalho entre
várias máquinas rodando ao mesmo tempo. Cada máquina faz uma fatia das buscas
e, ao final, juntamos tudo.

---

## Como funciona o pipeline

A coleta acontece em três fases:

```
Fase 1 — Coleta         Cada máquina busca suas palavras-chave no Glassdoor
                        e salva os resultados em CSVs (pasta data/bronze/).
                        ↓ todas enviam os CSVs para a Kethlen (Slack/Drive)

Fase 2 — Deduplicação   Só a Kethlen roda. Junta todos os CSVs, remove
                        duplicatas e gera um único arquivo de vagas únicas.
                        ↓ Kethlen envia de volta para todas as máquinas

Fase 3 — Enriquecimento Cada máquina visita as páginas de cada vaga para
                        coletar a descrição completa e as skills exigidas.
                        ↓ todas enviam os resultados para a Kethlen
                        ↓ Kethlen faz o merge final
```

A coleta usa um navegador Chrome real (não headless) para evitar bloqueios
automáticos do Glassdoor. O script imita comportamento humano: delays
aleatórios, scroll, fechamento de popups.

---

## Participantes e distribuição

| Máquina | Pessoa | Keywords buscadas | CSVs esperados (Fase 1) |
|---------|--------|-------------------|-------------------------|
| M1 ⭐   | MacBook Kethlen *(central)* | 0–26 (26 kw) | 702 |
| M2      | PC Inteli — Kethlen | 26–52 (26 kw) | 702 |
| M3      | Luana | 52–78 (26 kw) | 702 |
| M4      | Tati | 78–104 (26 kw) | 702 |
| M5      | Lucas | 104–128 (24 kw) | 648 |
| M6      | PC Inteli — Marco | 128–152 (24 kw) | 648 |
| M7      | PC Inteli — Scarpelin | 152–176 (24 kw) | 648 |
| M8      | Leo | 176–200 (24 kw) | 648 |

**Total:** 200 keywords × 27 estados = 5.400 buscas

---

## ⚠️ Regras durante a coleta (leia antes de começar)

O script roda em background, mas existem coisas que interrompem o processo.

### macOS (com tmux)

| Ação | Pode? |
|------|-------|
| Desligar a tela | ✅ Sim — configure para não suspender (ver abaixo) |
| Fechar o app Terminal | ✅ Sim — o tmux continua rodando |
| Usar o computador para outras coisas | ✅ Sim |
| Suspender / hibernar o Mac | ❌ Não — interrompe o processo |
| Fechar o laptop sem "nunca suspender" configurado | ❌ Não |
| Desligar ou reiniciar | ❌ Não |
| Fechar o terminal tmux sem desacoplar (`Ctrl+b d`) | ❌ Não |

**Para evitar suspensão automática no Mac:** use `caffeinate -i` antes do comando
`python` (incluído nos comandos abaixo). Ou: Ajustes do Sistema → Bateria →
desative "Ativar Power Nap" e defina tela como Nunca.

### Linux (com tmux)

| Ação | Pode? |
|------|-------|
| Fechar o terminal | ✅ Sim — tmux continua |
| Desligar a tela | ✅ Sim |
| Usar o computador para outras coisas | ✅ Sim |
| Suspender / hibernar | ❌ Não |
| Desligar ou reiniciar | ❌ Não |

### Windows (PowerShell)

| Ação | Pode? |
|------|-------|
| Desligar a tela | ✅ Sim — configure para nunca suspender (ver abaixo) |
| Minimizar o PowerShell | ✅ Sim |
| Usar o computador para outras coisas | ✅ Sim |
| Fechar a janela do PowerShell | ❌ Não — encerra o processo |
| Suspender, hibernar, desligar ou reiniciar | ❌ Não |

**Para evitar suspensão no Windows:** Painel de Controle → Opções de Energia →
"Colocar o computador em suspensão": **Nunca** (quando conectado).

> **Se o processo for interrompido:** não tem problema. Basta rodar o mesmo
> comando novamente — o script retoma de onde parou, pulando os CSVs que já
> existem.

---

## Pré-requisitos — antes de tudo

Antes de começar qualquer passo desta seção, você precisa ter **Git** e **Python**
instalados na sua máquina. Se já tiver os dois, pule direto para
[Clonar o repositório](#clonar-o-repositório).

---

### Instalar o Git

O Git é o programa que permite baixar o código do projeto para a sua máquina.

**macOS:**
```bash
# Opção 1 — via Homebrew (recomendado)
brew install git

# Opção 2 — via Xcode Command Line Tools
xcode-select --install
```
> Se não tiver o Homebrew: cole no terminal → `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

**Linux (Ubuntu / Debian):**
```bash
sudo apt update && sudo apt install git -y
```

**Windows:**
1. Acesse **https://git-scm.com/download/win** e baixe o instalador
2. Execute o instalador e clique em **Next** em todas as telas (as opções padrão funcionam)
3. Ao final, abra o **Git Bash** ou o **PowerShell** e confirme: `git --version`

---

### Instalar o Python

O script de coleta roda em Python 3.10 ou superior.

**macOS:**
```bash
brew install python
```

**Linux (Ubuntu / Debian):**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

**Windows:**
1. Acesse **https://www.python.org/downloads/** e baixe a versão mais recente
2. Execute o instalador; marque a opção **"Add Python to PATH"** antes de continuar
3. Clique em **Install Now**
4. Confirme no PowerShell: `python --version`

---

### Clonar o repositório

Depois de instalar o Git, baixe o código do projeto para a sua máquina.
Você só precisa fazer isso **uma vez**.

**macOS / Linux:**
```bash
git clone https://github.com/kethlenmartins/student-job.git
cd student-job
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/kethlenmartins/student-job.git
cd student-job
```

> **Onde fica o código?** Uma pasta chamada `2025-1A-T09-ES07-G02` será criada no
> diretório em que você rodou o comando. Os passos seguintes partem desse diretório.

---

## Máquina 1 — Kethlen ⭐ (máquina central)

Esta máquina faz a coleta normal (Fase 1) e também é a responsável por
centralizar os dados: receber os CSVs de todos, rodar a deduplicação e
distribuir o arquivo final para o enriquecimento (Fase 3).

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Rode cada comando abaixo em um terminal separado. Quando o Chrome abrir,
faça login no Glassdoor pelo botão "Continuar com Google" e pressione Enter
no terminal para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer

# Terminal 2 (abrir outro terminal)
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
# Terminal 1
tmux new -s t1
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 0 --kw-fim 13 \
  --perfil chrome-profile-t1 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d  para desacoplar

# Terminal 2
tmux new -s t2
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 13 --kw-fim 26 \
  --perfil chrome-profile-t2 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 0 --kw-fim 13 --perfil chrome-profile-t1 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 13 --kw-fim 26 --perfil chrome-profile-t2 --sem-enriquecer --assume-logged-in
```

Para ver o progresso (macOS/Linux): `tmux attach -t t1`. Para desacoplar: `Ctrl+b d`.

#### Passo 3 — Verificar se terminou

O script imprime `Coleta finalizada.` ao terminar. Para confirmar pelo número de arquivos:

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

---

### Entre Fase 1 e Fase 2 — Centralizar os CSVs

#### Passo 4 — Aguardar e receber os CSVs das outras máquinas

Quando cada pessoa terminar a Fase 1, ela vai te enviar os CSVs pelo Slack
(numa pasta do Drive ou os arquivos direto). Salve todos em `data/bronze/`.

> Só avance para o Passo 5 quando **todas as 8 máquinas** tiverem terminado.

#### Passo 5 — Deduplicação

**macOS / Linux:**
```bash
source venv/bin/activate
python deduplicar.py
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python deduplicar.py
```

O script vai imprimir os índices exatos para a Fase 3 de cada máquina:

```
Vagas únicas: 87.432
...
Índices para enriquecer.py  (16 terminais — 8 máquinas × 2):
===========================================================================
  M1 T1  MacBook Kethlen        --perfil chrome-profile-e1    --inicio 0       --fim 5465
  M1 T2  MacBook Kethlen        --perfil chrome-profile-e2    --inicio 5465    --fim 10930
  M2 T1  PC Inteli Kethlen      --perfil chrome-profile-e3    --inicio 10930   --fim 16395
  ...
```

#### Passo 6 — Distribuir para todas as máquinas

Envie no Slack para cada pessoa:
1. O arquivo `data/silver/vagas_unicas.csv`
2. Os índices `--inicio` e `--fim` específicos da máquina dela (copie da saída acima)

---

### Fase 3 — Enriquecimento

#### Passo 7 — Configurar perfis de enriquecimento (fazer uma vez)

> **⚠️ Sobre os valores entre colchetes:** `[SEU_INICIO_E1]`, `[SEU_FIM_E1]`,
> etc. são os índices impressos pelo `deduplicar.py` que você acabou de rodar.
> Procure as linhas "M1 T1" e "M1 T2" na saída e copie os valores de
> `--inicio` e `--fim` de cada uma. **Exemplo:** se a saída mostrar
> `--inicio 0 --fim 5465` para M1 T1, use esses números diretamente,
> sem os colchetes.

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [SEU_INICIO_E1] --fim [SEU_FIM_E1] --perfil chrome-profile-e1
# (outro terminal)
python enriquecer.py --inicio [SEU_INICIO_E2] --fim [SEU_FIM_E2] --perfil chrome-profile-e2
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [SEU_INICIO_E1] --fim [SEU_FIM_E1] --perfil chrome-profile-e1
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [SEU_INICIO_E2] --fim [SEU_FIM_E2] --perfil chrome-profile-e2
```

#### Passo 8 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e1
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [SEU_INICIO_E1] --fim [SEU_FIM_E1] \
  --perfil chrome-profile-e1 --assume-logged-in
# Ctrl+b d

tmux new -s e2
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [SEU_INICIO_E2] --fim [SEU_FIM_E2] \
  --perfil chrome-profile-e2 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [SEU_INICIO_E1] --fim [SEU_FIM_E1] --perfil chrome-profile-e1 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [SEU_INICIO_E2] --fim [SEU_FIM_E2] --perfil chrome-profile-e2 --assume-logged-in
```

#### Passo 9 — Aguardar todas as máquinas e fazer o merge final

Quando todas enviarem os arquivos `enriquecido_*.csv`, salve em `data/silver/` e rode:

**macOS / Linux:**
```bash
source venv/bin/activate
python mesclar.py
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python mesclar.py
```

Arquivo final: `data/silver/vagas_enriquecidas.csv`

---

---

## Máquina 2 — PC Inteli (Kethlen)

Você vai fazer a Fase 1 (coleta de vagas) e depois a Fase 3 (enriquecimento),
sempre a partir de instruções da Kethlen.

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t3
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 26 --kw-fim 39 \
  --perfil chrome-profile-t3 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t4
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 39 --kw-fim 52 \
  --perfil chrome-profile-t4 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 26 --kw-fim 39 --perfil chrome-profile-t3 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 39 --kw-fim 52 --perfil chrome-profile-t4 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

O script imprime `Coleta finalizada.` ao terminar.

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

#### Passo 4 — Enviar para a Kethlen

Quando ambos os terminais terminarem, envie a pasta `data/bronze/` para a
Kethlen no Slack — pode ser numa pasta do Google Drive ou enviando os CSVs
diretamente. Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_E3]` e `[FIM_E3]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 10930 --fim 16395`, seu comando fica:
> ```
> python enriquecer.py --inicio 10930 --fim 16395 --perfil chrome-profile-e3 --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

Coloque o `vagas_unicas.csv` dentro de `data/silver/`.

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:** copie o arquivo para `data\silver\` pelo explorador de arquivos ou:
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E3] --fim [FIM_E3] --perfil chrome-profile-e3
# (outro terminal)
python enriquecer.py --inicio [INICIO_E4] --fim [FIM_E4] --perfil chrome-profile-e4
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E3] --fim [FIM_E3] --perfil chrome-profile-e3
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E4] --fim [FIM_E4] --perfil chrome-profile-e4
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e3
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E3] --fim [FIM_E3] \
  --perfil chrome-profile-e3 --assume-logged-in
# Ctrl+b d

tmux new -s e4
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E4] --fim [FIM_E4] \
  --perfil chrome-profile-e4 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E3] --fim [FIM_E3] --perfil chrome-profile-e3 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E4] --fim [FIM_E4] --perfil chrome-profile-e4 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Quando terminar, envie os arquivos `data/silver/enriquecido_*.csv` para a
Kethlen no Slack (Drive ou direto).

---

---

## Máquina 3 — Luana

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 52 --kw-fim 65 --perfil chrome-profile-t5 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 65 --kw-fim 78 --perfil chrome-profile-t6 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 52 --kw-fim 65 --perfil chrome-profile-t5 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 65 --kw-fim 78 --perfil chrome-profile-t6 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t5
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 52 --kw-fim 65 \
  --perfil chrome-profile-t5 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t6
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 65 --kw-fim 78 \
  --perfil chrome-profile-t6 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 52 --kw-fim 65 --perfil chrome-profile-t5 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 65 --kw-fim 78 --perfil chrome-profile-t6 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:** copie para `data\silver\` ou:
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E5] --fim [FIM_E5] --perfil chrome-profile-e5
# (outro terminal)
python enriquecer.py --inicio [INICIO_E6] --fim [FIM_E6] --perfil chrome-profile-e6
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E5] --fim [FIM_E5] --perfil chrome-profile-e5
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E6] --fim [FIM_E6] --perfil chrome-profile-e6
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e5
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E5] --fim [FIM_E5] \
  --perfil chrome-profile-e5 --assume-logged-in
# Ctrl+b d

tmux new -s e6
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E6] --fim [FIM_E6] \
  --perfil chrome-profile-e6 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E5] --fim [FIM_E5] --perfil chrome-profile-e5 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E6] --fim [FIM_E6] --perfil chrome-profile-e6 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Máquina 4 — Tati

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 78 --kw-fim 91 --perfil chrome-profile-t7 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 91 --kw-fim 104 --perfil chrome-profile-t8 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 78 --kw-fim 91 --perfil chrome-profile-t7 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 91 --kw-fim 104 --perfil chrome-profile-t8 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t7
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 78 --kw-fim 91 \
  --perfil chrome-profile-t7 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t8
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 91 --kw-fim 104 \
  --perfil chrome-profile-t8 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 78 --kw-fim 91 --perfil chrome-profile-t7 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 91 --kw-fim 104 --perfil chrome-profile-t8 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **702**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **702**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:**
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E7] --fim [FIM_E7] --perfil chrome-profile-e7
# (outro terminal)
python enriquecer.py --inicio [INICIO_E8] --fim [FIM_E8] --perfil chrome-profile-e8
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E7] --fim [FIM_E7] --perfil chrome-profile-e7
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E8] --fim [FIM_E8] --perfil chrome-profile-e8
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e7
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E7] --fim [FIM_E7] \
  --perfil chrome-profile-e7 --assume-logged-in
# Ctrl+b d

tmux new -s e8
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E8] --fim [FIM_E8] \
  --perfil chrome-profile-e8 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E7] --fim [FIM_E7] --perfil chrome-profile-e7 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E8] --fim [FIM_E8] --perfil chrome-profile-e8 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Máquina 5 — Lucas

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 104 --kw-fim 116 --perfil chrome-profile-t9 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 116 --kw-fim 128 --perfil chrome-profile-t10 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 104 --kw-fim 116 --perfil chrome-profile-t9 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 116 --kw-fim 128 --perfil chrome-profile-t10 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t9
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 104 --kw-fim 116 \
  --perfil chrome-profile-t9 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t10
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 116 --kw-fim 128 \
  --perfil chrome-profile-t10 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 104 --kw-fim 116 --perfil chrome-profile-t9 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 116 --kw-fim 128 --perfil chrome-profile-t10 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **648**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **648**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:**
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E9] --fim [FIM_E9] --perfil chrome-profile-e9
# (outro terminal)
python enriquecer.py --inicio [INICIO_E10] --fim [FIM_E10] --perfil chrome-profile-e10
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E9] --fim [FIM_E9] --perfil chrome-profile-e9
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E10] --fim [FIM_E10] --perfil chrome-profile-e10
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e9
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E9] --fim [FIM_E9] \
  --perfil chrome-profile-e9 --assume-logged-in
# Ctrl+b d

tmux new -s e10
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E10] --fim [FIM_E10] \
  --perfil chrome-profile-e10 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E9] --fim [FIM_E9] --perfil chrome-profile-e9 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E10] --fim [FIM_E10] --perfil chrome-profile-e10 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Máquina 6 — PC Inteli (Marco)

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 128 --kw-fim 140 --perfil chrome-profile-t11 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 140 --kw-fim 152 --perfil chrome-profile-t12 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 128 --kw-fim 140 --perfil chrome-profile-t11 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 140 --kw-fim 152 --perfil chrome-profile-t12 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t11
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 128 --kw-fim 140 \
  --perfil chrome-profile-t11 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t12
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 140 --kw-fim 152 \
  --perfil chrome-profile-t12 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 128 --kw-fim 140 --perfil chrome-profile-t11 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 140 --kw-fim 152 --perfil chrome-profile-t12 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **648**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **648**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:**
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E11] --fim [FIM_E11] --perfil chrome-profile-e11
# (outro terminal)
python enriquecer.py --inicio [INICIO_E12] --fim [FIM_E12] --perfil chrome-profile-e12
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E11] --fim [FIM_E11] --perfil chrome-profile-e11
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E12] --fim [FIM_E12] --perfil chrome-profile-e12
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e11
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E11] --fim [FIM_E11] \
  --perfil chrome-profile-e11 --assume-logged-in
# Ctrl+b d

tmux new -s e12
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E12] --fim [FIM_E12] \
  --perfil chrome-profile-e12 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E11] --fim [FIM_E11] --perfil chrome-profile-e11 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E12] --fim [FIM_E12] --perfil chrome-profile-e12 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Máquina 7 — PC Inteli (Scarpelin)

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 152 --kw-fim 164 --perfil chrome-profile-t13 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 164 --kw-fim 176 --perfil chrome-profile-t14 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 152 --kw-fim 164 --perfil chrome-profile-t13 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 164 --kw-fim 176 --perfil chrome-profile-t14 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t13
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 152 --kw-fim 164 \
  --perfil chrome-profile-t13 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t14
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 164 --kw-fim 176 \
  --perfil chrome-profile-t14 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 152 --kw-fim 164 --perfil chrome-profile-t13 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 164 --kw-fim 176 --perfil chrome-profile-t14 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **648**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **648**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:**
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E13] --fim [FIM_E13] --perfil chrome-profile-e13
# (outro terminal)
python enriquecer.py --inicio [INICIO_E14] --fim [FIM_E14] --perfil chrome-profile-e14
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E13] --fim [FIM_E13] --perfil chrome-profile-e13
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E14] --fim [FIM_E14] --perfil chrome-profile-e14
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e13
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E13] --fim [FIM_E13] \
  --perfil chrome-profile-e13 --assume-logged-in
# Ctrl+b d

tmux new -s e14
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E14] --fim [FIM_E14] \
  --perfil chrome-profile-e14 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E13] --fim [FIM_E13] --perfil chrome-profile-e13 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E14] --fim [FIM_E14] --perfil chrome-profile-e14 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Máquina 8 — Leo

### Passo 0 — Setup (fazer uma vez)

**macOS / Linux:**
```bash
cd webscrapping-2026/webscrapping/versao3

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
playwright install chrome

brew install tmux    # macOS; Linux: sudo apt install tmux
```

**Windows (PowerShell):**
```powershell
cd webscrapping-2026\webscrapping\versao3

python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install chrome
```

---

### Fase 1 — Coleta

#### Passo 1 — Configurar perfis no Chrome (fazer uma vez)

Quando o Chrome abrir, faça login no Glassdoor pelo botão "Continuar com Google"
e pressione Enter para confirmar. Depois, encerre com Ctrl+C.

**macOS / Linux:**
```bash
source venv/bin/activate

# Terminal 1
python coleta_glassdoor.py --kw-inicio 176 --kw-fim 188 --perfil chrome-profile-t15 --sem-enriquecer

# Terminal 2 (outro terminal)
python coleta_glassdoor.py --kw-inicio 188 --kw-fim 200 --perfil chrome-profile-t16 --sem-enriquecer
```

**Windows (PowerShell):**
```powershell
# Terminal 1
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 176 --kw-fim 188 --perfil chrome-profile-t15 --sem-enriquecer
```
```powershell
# Terminal 2 (outra janela)
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 188 --kw-fim 200 --perfil chrome-profile-t16 --sem-enriquecer
```

#### Passo 2 — Rodar a coleta completa

**macOS / Linux (com tmux):**
```bash
tmux new -s t15
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 176 --kw-fim 188 \
  --perfil chrome-profile-t15 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d

tmux new -s t16
source venv/bin/activate
caffeinate -i python coleta_glassdoor.py \
  --kw-inicio 188 --kw-fim 200 \
  --perfil chrome-profile-t16 \
  --sem-enriquecer --assume-logged-in
# Ctrl+b d
```

**Windows (PowerShell):**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 176 --kw-fim 188 --perfil chrome-profile-t15 --sem-enriquecer --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python coleta_glassdoor.py --kw-inicio 188 --kw-fim 200 --perfil chrome-profile-t16 --sem-enriquecer --assume-logged-in
```

#### Passo 3 — Verificar se terminou

**macOS / Linux:** `ls data/bronze/*.csv | wc -l` → esperado: **648**

**Windows:** `(Get-ChildItem data\bronze\*.csv).Count` → esperado: **648**

#### Passo 4 — Enviar para a Kethlen

Envie a pasta `data/bronze/` para a Kethlen no Slack (Drive ou CSVs direto).
Avise quando tiver enviado.

---

### Fase 3 — Enriquecimento (aguardar sinal da Kethlen)

A Kethlen vai te enviar no Slack o arquivo `vagas_unicas.csv` e os índices
específicos para os seus dois terminais.

> **⚠️ Sobre os valores entre colchetes:** `[INICIO_Exx]` e `[FIM_Exx]` nos
> comandos abaixo são números que a Kethlen vai te mandar. Ela vai copiar a
> saída do script de deduplicação e enviar a linha exata com os valores para
> você. Substitua os colchetes pelos números recebidos, sem espaços extras.
> **Exemplo:** se ela mandar `--inicio 43716 --fim 49181`, seu comando fica:
> ```
> python enriquecer.py --inicio 43716 --fim 49181 --perfil chrome-profile-eXX --assume-logged-in
> ```

#### Passo 5 — Instalar o arquivo

**macOS / Linux:** `cp ~/Downloads/vagas_unicas.csv data/silver/`

**Windows:**
```powershell
Copy-Item $HOME\Downloads\vagas_unicas.csv data\silver\
```

#### Passo 6 — Configurar perfis de enriquecimento (fazer uma vez)

**macOS / Linux:**
```bash
source venv/bin/activate
python enriquecer.py --inicio [INICIO_E15] --fim [FIM_E15] --perfil chrome-profile-e15
# (outro terminal)
python enriquecer.py --inicio [INICIO_E16] --fim [FIM_E16] --perfil chrome-profile-e16
```

**Windows:**
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E15] --fim [FIM_E15] --perfil chrome-profile-e15
```
```powershell
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E16] --fim [FIM_E16] --perfil chrome-profile-e16
```

#### Passo 7 — Rodar o enriquecimento

**macOS / Linux (com tmux):**
```bash
tmux new -s e15
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E15] --fim [FIM_E15] \
  --perfil chrome-profile-e15 --assume-logged-in
# Ctrl+b d

tmux new -s e16
source venv/bin/activate
caffeinate -i python enriquecer.py \
  --inicio [INICIO_E16] --fim [FIM_E16] \
  --perfil chrome-profile-e16 --assume-logged-in
# Ctrl+b d
```

**Windows:**
```powershell
# Terminal 1 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E15] --fim [FIM_E15] --perfil chrome-profile-e15 --assume-logged-in
```
```powershell
# Terminal 2 — manter aberto
venv\Scripts\Activate.ps1
python enriquecer.py --inicio [INICIO_E16] --fim [FIM_E16] --perfil chrome-profile-e16 --assume-logged-in
```

*(os valores entre colchetes são os que a Kethlen vai enviar)*

#### Passo 8 — Enviar resultados para a Kethlen

Envie os arquivos `data/silver/enriquecido_*.csv` para a Kethlen no Slack.

---

---

## Referência rápida — tmux (macOS / Linux)

| Ação | Comando |
|------|---------|
| Criar sessão nomeada | `tmux new -s nome` |
| Desacoplar (processo continua) | `Ctrl+b d` |
| Reconectar | `tmux attach -t nome` |
| Listar sessões | `tmux ls` |
| Encerrar sessão | `tmux kill-session -t nome` |

---

## Resumo da distribuição

| Máquina | Pessoa | Fase 1 T1 | Fase 1 T2 | Fase 3 T1 | Fase 3 T2 | CSVs Fase 1 |
|---------|--------|-----------|-----------|-----------|-----------|-------------|
| M1 ⭐   | MacBook Kethlen | t1 (0–13) | t2 (13–26) | e1 | e2 | 702 |
| M2      | PC Inteli Kethlen | t3 (26–39) | t4 (39–52) | e3 | e4 | 702 |
| M3      | Luana | t5 (52–65) | t6 (65–78) | e5 | e6 | 702 |
| M4      | Tati | t7 (78–91) | t8 (91–104) | e7 | e8 | 702 |
| M5      | Lucas | t9 (104–116) | t10 (116–128) | e9 | e10 | 648 |
| M6      | PC Inteli Marco | t11 (128–140) | t12 (140–152) | e11 | e12 | 648 |
| M7      | PC Inteli Scarpelin | t13 (152–164) | t14 (164–176) | e13 | e14 | 648 |
| M8      | Leo | t15 (176–188) | t16 (188–200) | e15 | e16 | 648 |
