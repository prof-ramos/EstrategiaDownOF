# 📊 Plano: Sistema de Rastreamento de Downloads

## 🔍 Análise do Sistema Atual

### Sistema Existente: DownloadIndex (JSON)

**Localização:** `async_downloader.py:46-91`

**Implementação Atual:**

```python
class DownloadIndex:
    def __init__(self, base_dir: str):
        self.index_path = Path(base_dir) / "download_index.json"
        self.completed: set[str] = set()  # Set de caminhos de arquivos
        self._lock = threading.Lock()

    # Métodos: load(), save(), is_completed(), mark_completed()
```

**Formato do JSON:**

```json
{
  "completed": ["/path/to/Curso/Aula_01/Video_720p.mp4", "/path/to/Curso/Aula_01/PDF_Original.pdf"]
}
```

**Uso no código:**

- `main.py:288` - Modo síncrono
- `async_downloader.py:226` - Modo assíncrono
- Verifica antes de baixar: `if not index.is_completed(path) and not os.path.exists(path)`

---

## ⚠️ Limitações do Sistema Atual

### 1. **Falta de Metadados**

- ❌ Não armazena data/hora do download
- ❌ Não armazena tamanho do arquivo
- ❌ Não armazena URL original
- ❌ Não armazena hash/checksum para validação
- ❌ Não relaciona arquivo com curso/aula

### 2. **Sem Validação de Integridade**

- ❌ Não detecta arquivos corrompidos
- ❌ Não detecta arquivos deletados do disco
- ❌ Não verifica se o arquivo ainda existe

### 3. **Performance e Escalabilidade**

- ⚠️ Carrega todo o set na memória
- ⚠️ Salva o arquivo inteiro a cada `mark_completed()`
- ⚠️ Com milhares de arquivos pode ser lento

### 4. **Dificuldade de Consulta**

- ❌ Não permite queries como "todos os downloads de um curso"
- ❌ Não permite filtrar por data, tipo de arquivo, etc.
- ❌ Difícil debugar problemas

### 5. **Sem Histórico e Estatísticas**

- ❌ Não mantém histórico de tentativas
- ❌ Não rastreia erros de download
- ❌ Não fornece estatísticas (total baixado, tempo médio, etc.)

### 6. **Race Conditions Potenciais**

- ⚠️ Embora tenha locks, salvar em cada operação pode causar I/O excessivo
- ⚠️ Batch operations não são usadas consistentemente

---

## 🔄 Comparação de Soluções

### Opção 1: JSON Melhorado

**Prós:**

- ✅ Zero dependências externas
- ✅ Fácil de debugar (arquivo legível)
- ✅ Portável entre sistemas
- ✅ Backup simples (copiar arquivo)
- ✅ Compatível com sistema atual

**Contras:**

- ❌ Performance degrada com muitos arquivos (>10k)
- ❌ Sem queries complexas
- ❌ Carrega tudo na memória
- ❌ Writes frequentes podem ser lentos

**Melhorias possíveis:**

```json
{
  "version": "2.0",
  "downloads": {
    "/path/to/file.mp4": {
      "downloaded_at": "2025-12-31T10:30:00Z",
      "size_bytes": 104857600,
      "sha256": "abc123...",
      "url": "https://api.estrategia.../video.mp4",
      "course": "Curso de Python",
      "lesson": "Aula 01 - Introdução",
      "type": "video",
      "verified": true
    }
  },
  "statistics": {
    "total_files": 1,
    "total_bytes": 104857600,
    "last_sync": "2025-12-31T10:30:00Z"
  }
}
```

---

### Opção 2: SQLite ⭐ RECOMENDADO

**Prós:**

- ✅ Zero dependências (built-in no Python)
- ✅ Performance excelente mesmo com 100k+ registros
- ✅ Queries SQL complexas (filtros, joins, agregações)
- ✅ Transações ACID (atomicidade, consistência)
- ✅ Índices para buscas rápidas
- ✅ Menor uso de memória
- ✅ Writes são mais eficientes
- ✅ Backup simples (copiar arquivo .db)

**Contras:**

- ⚠️ Arquivo binário (não legível em editor de texto)
- ⚠️ Requer migration do sistema atual

**Schema proposto:**

```sql
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    url TEXT NOT NULL,
    course_name TEXT NOT NULL,
    lesson_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'video', 'pdf', 'material'
    size_bytes INTEGER,
    sha256 TEXT,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP,
    status TEXT DEFAULT 'completed',  -- 'completed', 'partial', 'error'
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

CREATE INDEX idx_course ON downloads(course_name);
CREATE INDEX idx_lesson ON downloads(lesson_name);
CREATE INDEX idx_type ON downloads(file_type);
CREATE INDEX idx_status ON downloads(status);

CREATE TABLE download_statistics (
    id INTEGER PRIMARY KEY,
    total_files INTEGER DEFAULT 0,
    total_bytes INTEGER DEFAULT 0,
    total_videos INTEGER DEFAULT 0,
    total_pdfs INTEGER DEFAULT 0,
    last_download_at TIMESTAMP,
    last_sync_at TIMESTAMP
);
```

---

### Opção 3: Banco de Dados Externo (PostgreSQL, MySQL)

**Prós:**

- ✅ Performance máxima em escala
- ✅ Suporte a múltiplos clientes
- ✅ Features avançadas

**Contras:**

- ❌ Requer servidor externo
- ❌ Dependências pesadas
- ❌ Configuração complexa
- ❌ Overkill para este projeto

**Veredicto:** ❌ **NÃO RECOMENDADO** - Complexidade desnecessária

---

### Opção 4: Pickle/Shelve

**Prós:**

- ✅ Built-in no Python
- ✅ Serialização rápida

**Contras:**

- ❌ Arquivo binário não portável
- ❌ Vulnerável a ataques (unpickling)
- ❌ Sem queries
- ❌ Difícil debugar

**Veredicto:** ❌ **NÃO RECOMENDADO** - Segurança e portabilidade

---

## 🎯 Solução Recomendada: SQLite com Fallback JSON

### Arquitetura Proposta

**Sistema Híbrido:**

1. **SQLite como principal** - Para performance e queries
2. **JSON como fallback** - Para compatibilidade e backup
3. **Migration automática** - Converte JSON antigo para SQLite
4. **Export JSON** - Permite exportar para debugging

### Estrutura de Arquivos

```text
/home/user/.../Estudo/Estrategia/
├── download_index.db        # SQLite database (novo)
├── download_index.json      # JSON backup (compatibilidade)
└── Meus Cursos/
    ├── Curso_Python/
    │   └── Aula_01/
    │       ├── Video_720p.mp4
    │       └── PDF_Original.pdf
    └── ...
```

---

## 🏗️ Implementação Proposta

### Fase 1: Criar Classe DownloadDatabase

**Novo arquivo:** `download_database.py`

```python
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import threading


class DownloadDatabase:
    """Sistema de rastreamento de downloads com SQLite + JSON backup."""

    def __init__(self, base_dir: str, use_sqlite: bool = True):
        self.base_dir = Path(base_dir)
        self.use_sqlite = use_sqlite
        self._lock = threading.Lock()

        if use_sqlite:
            self.db_path = self.base_dir / "download_index.db"
            self._init_sqlite()
        else:
            self.json_path = self.base_dir / "download_index.json"
            self._init_json()

    # Métodos principais:
    # - is_downloaded(file_path: str) -> bool
    # - mark_downloaded(file_path, url, course, lesson, file_type, size)
    # - verify_integrity(file_path: str) -> bool
    # - get_statistics() -> Dict
    # - get_downloads_by_course(course_name: str) -> List[Dict]
    # - export_to_json() -> str
    # - import_from_json(json_path: str)
```

### Fase 2: Migration do Sistema Antigo

**Features:**

- Auto-detecta `download_index.json` antigo
- Migra para SQLite preservando dados
- Mantém JSON como backup
- Compatibilidade total com código existente

### Fase 3: Verificação de Integridade

**Features:**

- Calcula SHA-256 dos arquivos baixados
- Verifica se arquivo ainda existe no disco
- Detecta arquivos corrompidos
- Permite re-download seletivo

### Fase 4: Estatísticas e Relatórios

**Features:**

- Total de arquivos baixados
- Total de bytes baixados
- Downloads por curso/aula
- Arquivos com erro
- Taxa de sucesso

---

## 📋 Plano de Implementação Detalhado

### Step 1: Criar `download_database.py`

**Tarefas:**

- [x] Criar classe `DownloadDatabase`
- [x] Implementar schema SQLite
- [x] Implementar métodos CRUD básicos
- [x] Adicionar thread-safety com locks
- [x] Implementar cálculo de hash SHA-256

**Arquivos afetados:**

- `download_database.py` (novo)

---

### Step 2: Migration Automática

**Tarefas:**

- [x] Implementar `migrate_from_json()`
- [x] Auto-detectar JSON antigo no `__init__`
- [x] Preservar dados durante migração
- [x] Criar backup antes de migrar

**Arquivos afetados:**

- `download_database.py`

---

### Step 3: Integração com Código Existente

**Tarefas:**

- [x] Substituir `DownloadIndex` por `DownloadDatabase` em `async_downloader.py`
- [x] Atualizar `main.py` para usar nova classe
- [x] Manter interface compatível (métodos is_completed, mark_completed)
- [x] Adicionar parâmetro `--use-json` para fallback

**Arquivos afetados:**

- `async_downloader.py` (modificar)
- `main.py` (modificar)

---

### Step 4: Verificação de Integridade

**Tarefas:**

- [x] Adicionar comando `--verify` para verificar downloads
- [ ] Adicionar comando `--redownload-corrupted` (planejado)

**Arquivos afetados:**

- `download_database.py`
- `main.py` (adicionar CLI args)

---

### Step 5: Estatísticas e Relatórios

**Tarefas:**

- [x] Implementar `get_statistics()`
- [x] Adicionar comando `--stats` para exibir estatísticas
- [x] Criar relatório em formato texto/JSON

**Arquivos afetados:**

- `download_database.py`
- `main.py` (adicionar CLI args)
- `ui.py` (adicionar formatação de stats)

---

### Step 6: Testes

**Tarefas:**

- [x] Criar `test_download_database.py`
- [x] Testar CRUD operations
- [x] Testar migration de JSON para SQLite
- [x] Testar thread-safety
- [x] Testar integridade de arquivos

**Arquivos afetados:**

- `test_download_database.py` (novo)

---

### Step 7: Documentação

**Tarefas:**

- [x] Atualizar README.md com novo sistema
- [x] Documentar comandos `--verify`, `--stats`
- [x] Adicionar exemplos de uso
- [x] Atualizar CHANGELOG.md

**Arquivos afetados:**

- `README.md`
- `CHANGELOG.md`

---

## 🔧 Interface da Nova Classe

### API Proposta

```python
# Inicialização
db = DownloadDatabase(base_dir="/path/to/downloads", use_sqlite=True)

# Verificar se arquivo já foi baixado
if db.is_downloaded("/path/to/file.mp4"):
    print("Já baixado")

# Marcar como baixado
db.mark_downloaded(
    file_path="/path/to/file.mp4",
    url="https://...",
    course_name="Curso de Python",
    lesson_name="Aula 01",
    file_type="video",
    size_bytes=104857600
)

# Verificar integridade
if not db.verify_integrity("/path/to/file.mp4"):
    print("Arquivo corrompido!")

# Estatísticas
stats = db.get_statistics()
print(f"Total: {stats['total_files']} arquivos, {stats['total_bytes']} bytes")

# Listar downloads de um curso
downloads = db.get_downloads_by_course("Curso de Python")
for d in downloads:
    print(f"{d['file_name']} - {d['downloaded_at']}")

# Export para JSON (backup/debug)
db.export_to_json("/path/to/backup.json")
```

---

## 🎁 Benefícios do Novo Sistema

### Performance

- ⚡ **10-100x mais rápido** em queries com muitos arquivos
- ⚡ **Menor uso de memória** - não carrega tudo de uma vez
- ⚡ **Writes mais eficientes** - transações em batch

### Funcionalidades

- 📊 **Estatísticas detalhadas** - total baixado, por curso, por tipo
- 🔍 **Queries avançadas** - filtrar por curso, data, tipo
- ✅ **Verificação de integridade** - detecta arquivos corrompidos
- 📝 **Histórico completo** - quando foi baixado, quantas tentativas

### Confiabilidade

- 🛡️ **Transações ACID** - dados sempre consistentes
- 🔒 **Thread-safe** - suporta downloads paralelos
- 💾 **Backup automático** - export JSON quando necessário
- 🔄 **Migration automática** - preserva dados antigos

### Manutenibilidade

- 🐛 **Debugging mais fácil** - queries SQL para investigar problemas
- 📦 **Zero dependências** - SQLite é built-in no Python
- 🔧 **Ferramentas existentes** - DB Browser for SQLite, etc.

---

## 🚀 Estratégia de Rollout

### Fase 1: Desenvolvimento e Testes (1-2 dias)

- Criar `download_database.py`
- Implementar testes unitários
- Testar migration

### Fase 2: Integração (1 dia)

- Integrar com `async_downloader.py` e `main.py`
- Testar com dados reais
- Garantir compatibilidade reversa

### Fase 3: Release (1 dia)

- Atualizar documentação
- Criar PR com mudanças
- Testar em ambiente real

---

## 🔄 Compatibilidade Reversa

### Garantias

- ✅ Sistema antigo continua funcionando com `--use-json`
- ✅ Migration automática preserva dados
- ✅ Interface compatível (is_completed, mark_completed)
- ✅ JSON backup sempre disponível

### Migration Path

```text
Primeira execução:
1. Detecta download_index.json
2. Cria download_index.db
3. Migra dados de JSON para SQLite
4. Mantém JSON como backup
5. Usa SQLite daqui pra frente
```

---

## 📊 Comparação Final

| Feature                  | JSON Atual | JSON Melhorado | SQLite (Recomendado) |
| ------------------------ | ---------- | -------------- | -------------------- |
| Performance (1k files)   | ⚠️ Médio   | ⚠️ Médio       | ✅ Excelente         |
| Performance (100k files) | ❌ Ruim    | ❌ Ruim        | ✅ Excelente         |
| Queries complexas        | ❌ Não     | ❌ Não         | ✅ Sim               |
| Metadados ricos          | ❌ Não     | ✅ Sim         | ✅ Sim               |
| Estatísticas             | ❌ Não     | ⚠️ Limitado    | ✅ Completo          |
| Verificação integridade  | ❌ Não     | ✅ Sim         | ✅ Sim               |
| Zero dependências        | ✅ Sim     | ✅ Sim         | ✅ Sim               |
| Debugging fácil          | ✅ Sim     | ✅ Sim         | ⚠️ Requer tool       |
| Thread-safe              | ✅ Sim     | ✅ Sim         | ✅ Sim               |
| Backup simples           | ✅ Sim     | ✅ Sim         | ✅ Sim (+ export)    |
| Uso de memória           | ❌ Alto    | ❌ Alto        | ✅ Baixo             |

---

## ✅ Recomendação Final

**Implementar SQLite com as seguintes características:**

1. ✅ **SQLite como padrão** - Performance e funcionalidades
2. ✅ **JSON como fallback** - Compatibilidade e debugging
3. ✅ **Migration automática** - Preserva dados antigos
4. ✅ **Export JSON** - Backup e portabilidade
5. ✅ **Interface compatível** - Zero breaking changes
6. ✅ **Verificação de integridade** - SHA-256 hash
7. ✅ **Estatísticas detalhadas** - Reports e analytics

**Esforço estimado:** 3-4 dias de desenvolvimento e testes

**Complexidade:** Média

**Risco:** Baixo (compatibilidade reversa garantida)

**Benefício:** Alto (performance + features + confiabilidade)

---

## 📝 Próximos Passos

1. **Revisar este plano** com stakeholders
2. **Aprovar arquitetura** proposta
3. **Criar branch** `feature/sqlite-tracking`
4. **Implementar Fase 1** (DownloadDatabase)
5. **Testar e iterar**
6. **Integrar com código existente**
7. **Release e documentação**

---

**Autor:** Claude Code

**Data:** 2025-12-31

**Versão:** 2.0 (Especificação)

**Status:** ✅ **ESPECIFICAÇÃO COMPLETA** (Aguardando implementação final de comandos de correção)
