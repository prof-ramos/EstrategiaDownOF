# 📚 AutoDownload Estratégia Concursos

> Downloader automático de cursos do Estratégia Concursos, otimizado para macOS.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Recursos Principais

- ⚡ **Downloads assíncronos ultra-rápidos** (modo padrão)
- 🔄 **Retry automático** com backoff exponencial (4 tentativas)
- 💾 **Resume de downloads** interrompidos (arquivos .part)
- ✅ **Sistema de tracking SQLite** com metadados ricos e estatísticas
- 🔐 **Login persistente** via cookies salvos
- 📦 **Downloads paralelos** configuráveis (padrão: 4 workers)
- 👻 **Modo headless** para rodar em segundo plano
- 🎨 **Interface CLI moderna e elegante** com ASCII art e cores
- 📊 **Progress bars** detalhadas com ícones Unicode
- 🔍 **Verificação de integridade** com hash SHA-256

## 🗄️ Sistema de Tracking SQLite (v2.0+)

O sistema foi completamente reformulado para usar **SQLite** em vez de JSON simples, oferecendo:

### 🎯 Vantagens

- **Performance 10-100x melhor** com muitos arquivos
- **Metadados ricos**: data, tamanho, URL, curso, aula, tipo de arquivo
- **Queries SQL**: filtrar por curso, data, tipo, etc.
- **Verificação de integridade**: SHA-256 hash para detectar corrupção
- **Estatísticas detalhadas**: total baixado, por curso, por tipo
- **Migration automática**: converte JSON antigo preservando dados
- **Compatibilidade reversa**: use `--use-json` para modo legado

### 📊 Novos Comandos

```bash
# Ver estatísticas de downloads
python main.py --stats

# Verificar integridade dos arquivos
python main.py --verify

# Usar modo JSON legado (se preferir)
python main.py --use-json
```

### 💡 Exemplo de Estatísticas

```
═══ ESTATÍSTICAS DE DOWNLOADS ═══

  📊 Total de arquivos: 1.234
  💾 Total de bytes: 45.678.901.234 (42.54 GB)
  🎥 Total de vídeos: 856
  📄 Total de PDFs: 234
  📚 Total de materiais: 144
  🕒 Último download: 2025-12-31 10:30:00

  Por curso:
    • Curso de Python: 456 arquivos (12.34 GB)
    • Curso de Java: 234 arquivos (8.76 GB)
    • Curso de JavaScript: 123 arquivos (5.43 GB)
```

### 🔍 Verificação de Integridade

O sistema pode verificar a integridade de todos os arquivos baixados:

```bash
python main.py --verify

# Saída:
🔍 Verificando integridade de 1.234 arquivos...
✓ Verificação completa:
  • Verificados: 1.230
  • Corrompidos: 2
  • Faltando: 2
```

### 🔄 Migration Automática

Na primeira execução com v2.0+, o sistema automaticamente:
1. Detecta `download_index.json` antigo
2. Cria `download_index.db` (SQLite)
3. Migra todos os dados preservando informações
4. Faz backup do JSON como `download_index.json.backup.TIMESTAMP`
5. Continua usando SQLite daqui pra frente

**Sem intervenção manual necessária!**

## 🎨 Interface Moderna

O downloader agora possui uma interface CLI elegante e profissional:

```
╭──────────────────────────────────────────────────────────────────╮
│                                                                  │
│     ███████╗███████╗████████╗██████╗  █████╗ ████████╗          │
│     ██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗╚══██╔══╝          │
│     █████╗  ███████╗   ██║   ██████╔╝███████║   ██║             │
│     ██╔══╝  ╚════██║   ██║   ██╔══██╗██╔══██║   ██║             │
│     ███████╗███████║   ██║   ██║  ██║██║  ██║   ██║             │
│     ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝             │
│                                                                  │
│              D O W N L O A D E R   v 2.0                         │
│                                                                  │
╰──────────────────────────────────────────────────────────────────╯
```

**Features visuais:**
- 📚 Headers com bordas arredondadas para cursos e aulas
- ⚡ Progress bars animadas com ícones Unicode
- ✓ Status coloridos (sucesso, aviso, erro)
- 📊 Painel de resumo ao final
- 🎯 Design limpo e profissional

**Demo da interface:**
```bash
python demo_ui.py
```

---

## 🚀 Início Rápido

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/EstrategiaDownloader.git
cd EstrategiaDownloader
```

### 2. Crie um ambiente virtual e instale as dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Execute o script

```bash
python main.py
```

Na primeira execução, o navegador abrirá para você fazer login. Após o login, os cookies serão
salvos automaticamente.

---

## ⚙️ Opções de Linha de Comando

| Argumento           | Descrição                                       | Padrão                                       |
| ------------------- | ----------------------------------------------- | -------------------------------------------- |
| `-d`, `--dir`       | Diretório para salvar os arquivos               | `~/Library/Mobile Documents/.../Meus Cursos` |
| `-w`, `--wait-time` | Tempo (segundos) para aguardar o login manual   | `60`                                         |
| `--headless`        | Executa o navegador em modo oculto (sem janela) | Desabilitado                                 |
| `--workers`         | Número de downloads simultâneos                 | `4`                                          |
| `--sync`            | Usa modo síncrono em vez de async (mais lento)  | Desabilitado (async é padrão)                |

### 🆕 Novidades da Versão Atual

- **Modo Async por padrão**: Muito mais rápido que o modo síncrono
- **Retry inteligente**: Se um download falhar (rede instável), tenta novamente automaticamente
- **Resume de downloads**: Se interromper o script, retoma de onde parou (arquivos `.part`)
- **Checkpoint persistente**: Salva em `download_index.json` quais arquivos já foram baixados

### Exemplos de Uso

**Uso básico (recomendado - modo async):**

```bash
python main.py
```

**Rodar em segundo plano (mais rápido):**

```bash
python main.py --headless
```

**Aumentar velocidade de download:**

```bash
python main.py --workers 8
```

**Salvar em um diretório personalizado:**

```bash
python main.py -d ~/Downloads/Cursos
```

**Usar modo síncrono (se tiver problemas com async):**

```bash
python main.py --sync
```

**Combinação recomendada (máxima velocidade):**

```bash
python main.py --headless --workers 8 -d ~/Downloads/Cursos
```

---

## 📁 Estrutura de Arquivos Baixados

```
Meus Cursos - Estratégia Concursos/
├── Nome_do_Curso/
│   ├── Aula_01_Introducao/
│   │   ├── Assuntos.txt
│   │   ├── Aula_01_PDF_Original.pdf
│   │   ├── Aula_01_PDF_Simplificado.pdf
│   │   ├── Video_Titulo_720p.mp4
│   │   └── Video_Titulo_Resumo_0.pdf
│   └── Aula_02_Conceitos/
│       └── ...
└── Outro_Curso/
    └── ...
```

---

## 🛡️ Sistema de Resiliência

### Retry Automático com Backoff Exponencial

Se um download falhar devido a problemas de rede, o sistema tenta novamente automaticamente:

- **1ª tentativa**: Imediato
- **2ª tentativa**: Aguarda 2 segundos
- **3ª tentativa**: Aguarda 4 segundos
- **4ª tentativa**: Aguarda 8 segundos

### Resume de Downloads Interrompidos

Se você interromper o script (Ctrl+C) ou ocorrer um erro:

1. Arquivos completos são salvos em `download_index.json`
2. Downloads parciais são salvos como `.part` files
3. Na próxima execução, continua de onde parou

**Exemplo:**
```bash
# Primeira execução (interrompida)
python main.py
# Ctrl+C durante download de video.mp4
# Arquivo salvo como: video.mp4.part (parcial)

# Segunda execução (retoma automaticamente)
python main.py
# Retoma o download de video.mp4 de onde parou!
```

### Limpeza de Arquivos Temporários

Se quiser recomeçar tudo do zero:

```bash
# Remove checkpoint e arquivos parciais
rm download_index.json
rm **/*.part

# Executa novamente
python main.py
```

---

## 🔧 Resolução de Problemas

### O navegador não abre

**Certifique-se de que o Chrome ou Edge está instalado:**

```bash
# Verificar Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

### Erro de certificado SSL

Este script já desabilita a verificação SSL automaticamente. Se ainda assim tiver problemas, tente:

```bash
pip install --upgrade certifi
```

### Cookies não funcionam / Sessão expira

Delete o arquivo `cookies.json` e faça login novamente:

```bash
rm cookies.json
python main.py
```

### Download muito lento

Aumente o número de workers:

```bash
python main.py --workers 8
```

> ⚠️ **Atenção:** Muitos workers podem sobrecarregar sua conexão ou ser bloqueados pelo servidor.

---

## 📋 Requisitos

- **Python** 3.9 ou superior
- **Google Chrome** ou **Microsoft Edge**
- **Conta ativa** no Estratégia Concursos

### Dependências Python

- `requests` - Requisições HTTP síncronas
- `aiohttp` - Requisições HTTP assíncronas (modo async)
- `aiofiles` - I/O de arquivos assíncrono
- `tqdm` - Barras de progresso
- `colorama` - Cores no terminal
- `selenium` - Automação do navegador

---

## 🏗️ Arquitetura

```mermaid
flowchart TD
    A[Início] --> B{Cookies existem?}
    B -->|Sim| C[Carregar sessão]
    B -->|Não| D[Aguardar login manual]
    C --> E{Sessão válida?}
    E -->|Não| D
    E -->|Sim| F[Listar cursos]
    D --> G[Salvar cookies]
    G --> F
    F --> H[Para cada curso]
    H --> I[Listar aulas]
    I --> J[Para cada aula]
    J --> K[Coletar links - Serial]
    K --> L[Baixar arquivos - Paralelo]
    L --> J
    J --> H
    H --> M[Fim]
```

---

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## ⚠️ Aviso Legal

Este projeto é apenas para **uso pessoal e educacional**. Respeite os termos de uso do Estratégia
Concursos. O desenvolvedor não se responsabiliza pelo uso indevido desta ferramenta.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
