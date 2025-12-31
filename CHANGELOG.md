# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

## [2.0.0] - 2025-12-31

### 🎉 MAJOR: Sistema de Tracking SQLite

**Breaking Change:** O sistema de tracking agora usa SQLite por padrão em vez de JSON simples.

### ✨ Adicionado
- **Sistema SQLite completo** (`download_database.py`) com:
  - Metadados ricos (data, tamanho, URL, curso, aula, tipo)
  - Performance 10-100x melhor com muitos arquivos
  - Queries SQL complexas (filtrar por curso, data, tipo)
  - Verificação de integridade com SHA-256
  - Estatísticas detalhadas (total, por curso, por tipo)
  - Migration automática do JSON antigo
  - Thread-safe com locks
  - Export/Import JSON para backup

- **Novos comandos CLI:**
  - `--stats`: Mostra estatísticas de downloads e sai
  - `--verify`: Verifica integridade dos arquivos (SHA-256)
  - `--use-json`: Usa tracking JSON legado em vez de SQLite

- **Testes completos** em `test_download_database.py`:
  - Operações básicas CRUD
  - Migration JSON → SQLite
  - Verificação de integridade SHA-256
  - Batch operations
  - Queries e estatísticas

### 🔄 Modificado
- `async_downloader.py`: Suporte a `DownloadDatabase` com metadados
- `main.py`: Integração completa com SQLite e novos comandos
- Todos os tasks de download agora incluem metadados (course_name, lesson_name, file_type)
- `DownloadIndex` marcado como DEPRECATED (mantido para compatibilidade)

### ⚡ Melhorias de Performance
- Tracking SQLite é 10-100x mais rápido que JSON com muitos arquivos
- Menor uso de memória (não carrega tudo de uma vez)
- Writes mais eficientes com transações em batch
- Índices otimizados para queries rápidas

### 🛡️ Confiabilidade
- Migration automática preserva dados antigos
- Backup automático do JSON antigo
- Compatibilidade reversa com --use-json
- Transações ACID garantem consistência
- Detecção de arquivos corrompidos ou deletados

### 📊 Features de Análise
- Estatísticas por curso, tipo de arquivo, e data
- Histórico completo de downloads
- Verificação de integridade de arquivos
- Export para JSON para análise externa

---

## [Unreleased]

### ✨ Adicionado
- **Retry automático com backoff exponencial** (4 tentativas: 2s → 4s → 8s → 16s)
- **Sistema de checkpoint/resume** no modo síncrono usando `DownloadIndex`
- **Resume de downloads parciais** com arquivos `.part` em ambos os modos
- **Retry com backoff** no modo async
- **Modo async como padrão** para melhor performance (--sync para usar síncrono)
- Suite de testes em `test_improvements.py`
- Seção "Sistema de Resiliência" no README.md

### 🔄 Modificado
- `main.py`: Integração de retry e checkpoint no modo síncrono
- `async_downloader.py`: Adicionado retry loop com backoff exponencial
- `README.md`: Documentação completa das novas features
- `requirements.txt`: Adicionadas dependências `aiohttp>=3.9.0` e `aiofiles>=23.2.0`
- Interface de linha de comando com informações de retry e checkpoint

### 🐛 Corrigido
- Downloads não eram retentados em caso de falha de rede
- Progresso era perdido ao interromper downloads no modo síncrono
- Arquivos parciais não eram retomados no modo síncrono

### ⚡ Melhorias de Performance
- Modo async agora é o padrão (5x+ mais rápido que síncrono)
- Downloads podem ser retomados de onde pararam (HTTP Range requests)
- Checkpoint evita re-download de arquivos completos

## [1.0.0] - 2025-12-31

### ✨ Adicionado
- Download automático de cursos do Estratégia Concursos
- Login persistente via cookies salvos
- Downloads paralelos configuráveis (padrão: 4 workers)
- Modo headless para execução em segundo plano
- Progress bars detalhadas com cores
- Suporte a Chrome e Edge
- Otimizações para macOS

### 📚 Documentação
- README.md completo com exemplos
- Instruções de instalação e uso
- Resolução de problemas comuns
