# Magazord Test Runner (HTML) — Guia de uso (BETA)

> Interface local para **navegar nos arquivos**, **executar Robot Framework por TAG** e **visualizar respostas teóricas** em **Markdown/PDF**.

---
## Execução do sistema
- O executável ficará em `dist\TesteMagazord\TesteMagazord.exe`.

Ao executar o EXE:
- ele sobe o servidor local
- e abre a tela HTML no navegador padrão
> Status: **BETA** — desenvolvido em prazo curto, então alguns cenários podem não ter sido totalmente testados.

## Visão geral

Este projeto sobe um servidor local e abre uma **tela HTML** para:

- Navegar pela **estrutura de pastas** do teste
- Executar Robot Framework por **TAG** (`robot -i TAG`)
- Visualizar **report/log** gerados (preview na própria tela)
- Listar e visualizar **respostas teóricas (.md)** com **preview em PDF** (gerado automaticamente)

---

## 1) Pré-requisitos

- **Windows** (necessário para o `.exe`)
- **Python 3.10+**
- **Robot Framework** instalado (ou via `requirements.txt` do seu teste)

Instale as dependências da aplicação (UI):

```bash
pip install -r requirements_app.txt
```

> Dica: mesmo que você instale o `requirements.txt` do teste, instale também o `requirements_app.txt` (ele inclui a UI e libs de suporte).

---

## 2) Executar a tela (modo Python)

Dentro da pasta do projeto:

```bash
python app/main.py
```

O app abrirá automaticamente no navegador em:

- `http://127.0.0.1:8765`

### Observações importantes (primeira execução)
- A **primeira execução** pode demorar alguns segundos para extrair/carregar dados.
- Pode ocorrer **timeout** na primeira tentativa; se acontecer, **feche e execute novamente**.
- A mensagem de “não foi possível conectar” pode aparecer durante o carregamento inicial — aguarde e tente novamente.

---

## 3) Como funciona

### 3.1 Menu Geral (execução por TAG)

Fluxo típico:

1. Selecione uma pasta (ex.: `parte2-e2e/questao2.1`)
2. Escolha uma **TAG**
3. Clique em **Executar**

O app executa:

```bash
robot -i TAG -d app/static/runs/<run_id> <suite>
```

Depois disso, o sistema disponibiliza o preview de:

- `report.html`
- `log.html`

**Arquivos úteis da execução** (sempre gerados quando possível):

- `app/static/runs/<run_id>/console_stdout.txt`
- `app/static/runs/<run_id>/console_stderr.txt`

### 3.2 Menu Respostas teóricas (Markdown / PDF)

- Lista `RESPOSTA_TEORICA.md` e `readme.md`
- Ao clicar em **PDF**, o servidor gera e mostra um PDF no preview (ReportLab)
- Você pode **baixar** o PDF gerado

> Se alguma linha “quebrar” ou ficar cortada no PDF, normalmente é ajuste de quebra/word-wrap no gerador do ReportLab.

---

## 4) Trocar o ZIP do teste (opcional)

O app já vem com um ZIP embutido em:

- `app/static/assets/magazord.zip`

Para substituir:

1. Troque o arquivo `magazord.zip` por outro **com a mesma estrutura**
2. Rode novamente o app

---

## 5) Build para EXE (Windows)

### Opção A) Executável que abre o navegador (mais simples)

Instale o PyInstaller:

```bash
pip install pyinstaller
```

Gere o `.exe`:

```bash
pyinstaller --noconsole --onefile ^
  --add-data "app/static;app/static" ^
  app/main.py
```

O executável ficará em `dist/main.exe`.

Ao executar o EXE:
- ele sobe o servidor local
- e abre a tela HTML no navegador padrão

### Opção B) EXE com janela (sem navegador) — *pywebview* (opcional)

Se quiser abrir a UI dentro do exe (janela nativa), instale:

```bash
pip install pywebview
```

Depois, adapte o `app/main.py` para abrir via `webview.create_window(...)`.

---

## 6) Funcionalidades do sistema

### Menu Geral
- **Navegação de Arquivos**: visualiza toda a estrutura de arquivos das questões
- **Visualização de Código**: selecione um arquivo e clique em “Abrir Código”
- **Log de Execução**: após executar um teste, clique em “Abrir Log” para visualizar resultado
- **Rodar Regression**: executa todas as questões de teste automatizado em sequência

### Menu Respostas Teóricas
- Lista respostas por pasta
- Formatos:
  - 📄 **MD**: abre o Markdown
  - 📑 **PDF**: abre o PDF gerado
  - ⬇️ **Download PDF**: baixa o PDF

### Botões do sistema
- **Verificar Ambiente**: valida Python/Node, libs e configurações necessárias
- **Instalar Requirements**: instala dependências necessárias (Python/Node, etc.)
- **Recarregar**: recarrega a página

---

## 7) Solução de problemas

### “robot não encontrado”
- Use um **venv** e instale Robot nele, ou garanta que o `robot` esteja no `PATH`.

### Execução não gera `log.html`/`report.html`
- Verifique os arquivos de console:
  - `app/static/runs/<run_id>/console_stdout.txt`
  - `app/static/runs/<run_id>/console_stderr.txt`

### Lentidão / primeira carga
- Normal em BETA quando há extração de ZIP e preparação de cache na primeira execução.

---

## 8) Estrutura do projeto

```text
magazord_runner/
  app/
    main.py
    static/
      index.html
      assets/
        magazord.zip
      runs/
    data/
      TesteMagazord/   (extraído automaticamente)
      _pdf_cache/
  requirements_app.txt
```

---

## Notas

- Projeto em evolução (BETA).
- Caso encontre falhas, consulte os logs e reporte o cenário (menu, ação, arquivo/pasta, mensagem de erro).
