# 🗺️ Roadmap - EstrategiaDownOF

Este documento detalha o planejamento de features futuras e melhorias previstas para o projeto.

## 📌 Legenda

- ✅ Implementado
- 🚧 Em desenvolvimento
- 📋 Planejado
- 💡 Ideia / Proposta
- ❌ Descartado

---

## 🎯 Versão 2.0.0 (Atual) - ✅ Lançada

### Features Principais
- ✅ Sistema de tracking SQLite com metadados ricos
- ✅ Downloads assíncronos com aiohttp
- ✅ Retry automático com backoff exponencial
- ✅ Resume de downloads com arquivos `.part`
- ✅ Compressão automática de vídeos (FFmpeg)
- ✅ Verificação de integridade (SHA-256)
- ✅ Estatísticas detalhadas (`--stats`)
- ✅ Interface CLI moderna com cores

### Infraestrutura
- ✅ GitHub Actions CI/CD
- ✅ Pre-commit hooks
- ✅ Docker e Docker Compose
- ✅ Makefile com comandos úteis
- ✅ Documentação completa (README, FAQ, CONTRIBUTING, SECURITY)

---

## 🚀 Versão 2.1.0 - 📋 Próxima Release (Q1 2026)

### 🎯 Foco: Usabilidade e Segurança

#### Features de Usuário
- 📋 **Filtros de download** (`--only-videos`, `--only-pdfs`, `--exclude-materials`)
  - Baixar apenas tipos específicos de arquivo
  - Filtrar por curso, data, professor
  - Configurável via CLI e config.yaml

- 📋 **Seleção de cursos**
  - Menu interativo para escolher cursos
  - Regex/pattern matching para filtrar cursos
  - Exemplo: `--courses "Python|JavaScript"`

- 📋 **Dry-run mode** (`--dry-run`)
  - Simula downloads sem efetivamente baixar
  - Mostra preview de arquivos e tamanho total
  - Útil para estimar espaço necessário

- 📋 **Resumo pós-download**
  - Dashboard final com estatísticas
  - Total baixado, tempo decorrido, velocidade média
  - Economia de espaço com compressão

- 📋 **Rate limiting configurável**
  - Respeitar limites do servidor
  - Configurável via `--rate-limit <req/min>`
  - Delay mínimo entre requisições

#### Segurança
- 📋 **Criptografia de cookies** (AES-256)
  - Cookies armazenados criptografados
  - Senha mestra via variável de ambiente
  - Migração automática de cookies existentes

- 📋 **Flag `--verify-ssl`**
  - SSL verification opcional (padrão: desabilitado)
  - Permite uso em ambientes corporativos
  - Warning claro quando desabilitado

- 📋 **Validação rigorosa de paths**
  - Prevenir path traversal attacks
  - Sanitização completa de filenames
  - Whitelist de extensões permitidas

#### DX (Developer Experience)
- 📋 **Testes de integração E2E**
  - Testes com mock do Estratégia
  - Cobertura > 80%
  - CI/CD automatizado

- 📋 **Logs estruturados JSON**
  - Facilita parsing e monitoramento
  - Integração com ELK stack
  - Níveis de log configuráveis

---

## 🔮 Versão 2.2.0 - 💡 Futuro (Q2 2026)

### 🎯 Foco: Features Avançadas

#### UI e UX
- 💡 **Interface Web (opcional)**
  - Dashboard web para monitoramento
  - Controle remoto de downloads
  - Visualização de estatísticas
  - Framework: FastAPI + React

- 💡 **TUI (Terminal UI)**
  - Interface interativa no terminal
  - Usando `rich` ou `textual`
  - Progress bars em tempo real
  - Navegação por cursos/aulas

- 💡 **Notificações desktop**
  - Alerta ao completar curso
  - Alerta ao completar todos os downloads
  - Usando `plyer` ou `notify-send`

#### Integrações
- 💡 **Sync com cloud storage**
  - Google Drive, Dropbox, OneDrive
  - Upload automático pós-download
  - Configurável por curso

- 💡 **Webhooks**
  - Notificar sistemas externos
  - Integração com Discord, Slack, Telegram
  - Eventos: download completo, erro, etc.

- 💡 **API REST**
  - Controle programático do downloader
  - Endpoints para stats, control, config
  - Autenticação JWT

#### Performance
- 💡 **Download paralelo de chunks**
  - Acelerar downloads de arquivos grandes
  - HTTP Range requests em múltiplas conexões
  - Similar ao aria2c

- 💡 **Cache inteligente**
  - Redis para metadados
  - Cache de sessões Selenium
  - Reduzir requisições repetidas

- 💡 **Compressão em real-time**
  - Comprimir durante o download
  - Economizar espaço de disco
  - Usando pipe FFmpeg

---

## 🌟 Versão 3.0.0 - 💡 Visão de Longo Prazo (2027+)

### 🎯 Foco: Plataforma Completa

#### Multi-plataforma
- 💡 **Suporte a outras plataformas**
  - Gran Cursos
  - CERS
  - Cursos online genéricos
  - Plugin system para novas plataformas

- 💡 **Plugin architecture**
  - Sistema de plugins para parsers
  - Plugins da comunidade
  - Marketplace de plugins

#### ML e AI
- 💡 **Transcrição automática** (Whisper)
  - Gerar legendas para vídeos
  - Busca por conteúdo de vídeos
  - Suporte a múltiplos idiomas

- 💡 **Resumos com IA**
  - Resumir PDFs e vídeos
  - Gerar flashcards automaticamente
  - Usando LLMs locais (llama.cpp)

- 💡 **Detecção de duplicatas**
  - Identificar conteúdo duplicado
  - Deduplicação inteligente
  - Economizar espaço

#### Colaboração
- 💡 **Compartilhamento de metadados**
  - Database compartilhado de cursos
  - Crowdsourced metadata
  - Sem compartilhar conteúdo (apenas metadados)

- 💡 **Sistema de reviews**
  - Avaliar cursos e professores
  - Comentários e notas
  - Ranking de melhores materiais

---

## ❌ Descartados

### Features que não serão implementadas

- ❌ **Suporte a Python < 3.9**
  - Razão: Dependências modernas requerem 3.9+
  - Alternativa: Use container Docker com Python 3.11

- ❌ **Download de exercícios online**
  - Razão: Requer automação complexa, viola ToS
  - Alternativa: Use a plataforma web

- ❌ **Bypass de DRM**
  - Razão: Ilegal, viola ToS
  - Alternativa: N/A

- ❌ **Integração com HF Run Job**
  - Razão: Bottleneck é rede, não CPU (veja FAQ)
  - Alternativa: Otimizações locais

---

## 📊 Priorização

### P0 (Crítico) - v2.1.0
1. Filtros de download
2. Dry-run mode
3. Criptografia de cookies
4. Testes E2E

### P1 (Importante) - v2.1.0-v2.2.0
1. Seleção interativa de cursos
2. Rate limiting
3. Notificações desktop
4. TUI

### P2 (Nice to have) - v2.2.0+
1. Interface web
2. API REST
3. Cloud sync
4. Webhooks

### P3 (Futuro distante) - v3.0.0+
1. Multi-plataforma
2. ML/AI features
3. Plugin system

---

## 🤝 Como Contribuir para o Roadmap

### Sugerir Features
1. Abra uma [Discussion](https://github.com/prof-ramos/EstrategiaDownOF/discussions)
2. Use o template "Feature Request"
3. Descreva caso de uso e motivação

### Votar em Features
- ⭐ Dê star em issues de features desejadas
- 💬 Comente com seu caso de uso
- 👍 Reaja com 👍 em features prioritárias

### Implementar Features
1. Escolha uma feature marcada como 📋 Planejada
2. Abra uma issue "Implementing: [Feature Name]"
3. Siga [CONTRIBUTING.md](CONTRIBUTING.md)
4. Abra PR com referência à issue

---

## 📅 Timeline Estimado

| Versão | Release Target | Status |
|--------|----------------|--------|
| 2.0.0  | 2025-12-31     | ✅ Lançado |
| 2.1.0  | 2026-03-31     | 📋 Planejado |
| 2.2.0  | 2026-06-30     | 💡 Proposto |
| 3.0.0  | 2027+          | 💡 Visão |

**Nota:** Datas são estimativas e podem mudar conforme feedback da comunidade e disponibilidade de recursos.

---

## 📞 Feedback

Tem sugestões? Entre em contato:

- 📧 Email: prof.ramos@example.com
- 💬 Discussions: [GitHub Discussions](https://github.com/prof-ramos/EstrategiaDownOF/discussions)
- 🐛 Bugs/Features: [GitHub Issues](https://github.com/prof-ramos/EstrategiaDownOF/issues)

**Última atualização:** 2026-01-01
