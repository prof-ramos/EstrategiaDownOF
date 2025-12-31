# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

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
