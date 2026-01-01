# ❓ Perguntas Frequentes (FAQ)

## 📚 Geral

### O que é o EstrategiaDownOF?

EstrategiaDownOF é um downloader automático otimizado para cursos do Estratégia Concursos. Ele baixa vídeos, PDFs e materiais complementares de forma eficiente, com retry automático, resume de downloads e tracking SQLite.

### É legal usar este software?

Este projeto é destinado **exclusivamente para uso pessoal e educacional**. Você deve:
- Ter uma assinatura válida do Estratégia Concursos
- Respeitar os termos de uso da plataforma
- Usar os materiais apenas para estudo pessoal
- **NÃO** distribuir ou revender os conteúdos baixados

### Funciona em quais sistemas operacionais?

- ✅ **macOS** (testado e otimizado)
- ✅ **Linux** (Ubuntu, Debian, Fedora, etc.)
- ⚠️ **Windows** (funciona, mas com limitações no uvloop)

### Preciso de conta paga?

Sim, você precisa ter uma assinatura ativa do Estratégia Concursos para fazer login e acessar os cursos.

## 🚀 Instalação e Setup

### Como instalo o Python 3.9+?

**macOS:**
```bash
# Usando Homebrew
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

**Windows:**
Baixe do [python.org](https://www.python.org/downloads/)

### Erro: "Chrome not found"

**Solução:**
```bash
# macOS
brew install --cask google-chrome

# Linux
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```

### Como instalo o FFmpeg?

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg  # Fedora
```

**Windows:**
Baixe de [ffmpeg.org](https://ffmpeg.org/download.html)

## 💾 Downloads e Armazenamento

### Quanto espaço em disco preciso?

Depende dos seus cursos:
- **Vídeo 720p**: ~200-500 MB/hora
- **PDF**: ~5-50 MB por arquivo
- **Materiais**: ~1-10 MB por arquivo

**Exemplo:** Um curso de 40 horas pode ocupar ~15-20 GB.

### Posso pausar e continuar depois?

**Sim!** O sistema possui:
- **Resume automático**: Arquivos `.part` são retomados
- **Checkpoint**: `download_index.db` rastreia o que já foi baixado
- Basta interromper (Ctrl+C) e rodar novamente

### Como libero espaço sem perder progresso?

```bash
# 1. Comprima os vídeos
make compress

# 2. Verifique economia de espaço
du -sh downloads/

# 3. (Opcional) Delete vídeos originais
# Se usou --delete na compressão, já foram deletados
```

### O que é o arquivo `download_index.db`?

É o banco de dados SQLite que rastreia:
- Quais arquivos foram baixados
- Metadados (curso, aula, tipo, tamanho, data)
- Hash SHA-256 para verificação de integridade

**Importante:** Não delete este arquivo ou você perderá o histórico!

### Como faço backup do progresso?

```bash
# Backup do database
make backup-db

# Backup manual com timestamp
cp download_index.db "download_index.db.backup.$(date +%Y%m%d_%H%M%S)"
```

## ⚙️ Configuração e Uso

### Como aumento a velocidade de download?

```bash
# Aumente o número de workers
python main.py --workers 12

# Use modo async (já é padrão)
# E rode em headless
python main.py --headless --workers 12
```

**Atenção:** Muitos workers podem:
- Sobrecarregar sua conexão
- Ser bloqueados pelo servidor
- Causar instabilidade

Recomendado: **4-8 workers** para conexões normais.

### Como baixo apenas PDFs?

Atualmente não há flag nativa, mas você pode:

**Opção 1:** Editar `main.py` para filtrar por tipo
**Opção 2:** Usar a funcionalidade de config (planejado para v2.1)

```yaml
# config.yaml (futuro)
filters:
  file_types: [pdf]
```

### Posso selecionar cursos específicos?

Não nativamente na v2.0. Planejado para v2.1:

```yaml
# config.yaml (futuro)
filters:
  courses: ["Direito Constitucional", "Python"]
```

**Workaround atual:** Baixe tudo e delete o que não quer.

### Como desabilito a compressão automática?

Edite `main.py` e comente as linhas 944-949:

```python
# Após terminar todas as aulas do curso, comprime os vídeos
# try:
#     compress_course_videos(save_dir, course['title'])
# except Exception as comp_error:
#     log_error(f"Falha na compressão do curso '{course['title']}': {comp_error}")
```

Ou aguarde v2.1 com flag `--no-compress`.

## 🔧 Troubleshooting

### "Session expired. Login manual necessário"

**Causa:** Cookies expiraram ou foram invalidados.

**Solução:**
```bash
# Delete cookies e faça login novamente
rm cookies.json
python main.py
# Aguarde 60s para fazer login
```

### Downloads muito lentos

**Possíveis causas:**
1. **Conexão lenta**: Teste sua velocidade
2. **Servidor limitando**: Reduza workers
3. **Disco cheio**: Verifique `df -h`

**Soluções:**
```bash
# Teste velocidade
speedtest-cli

# Reduza workers
python main.py --workers 2

# Verifique espaço
df -h ~/Downloads
```

### "No space left on device"

**Solução:**
```bash
# 1. Verifique espaço
df -h

# 2. Libere espaço
rm -rf ~/.Trash/*  # macOS
sudo apt clean      # Linux

# 3. Mude diretório de download
python main.py -d /mnt/disco_externo/Cursos
```

### Erro de SSL/certificado

O script já desabilita verificação SSL por padrão. Se ainda assim houver erro:

```bash
# Atualizar certificados
pip install --upgrade certifi
```

### Vídeos corrompidos após compressão

**Verificação:**
```bash
# Verifica integridade
python main.py --verify
```

**Prevenção:**
- Não interrompa durante compressão
- Use `--quality high` para menos agressividade
- Não use `--delete` até confirmar que funcionou

## 🐳 Docker

### Como rodo no Docker?

```bash
# Build
docker-compose build

# Run
docker-compose up

# Com compressão
docker-compose --profile compression up
```

### Como acesso os arquivos baixados?

Estão no diretório `./downloads` do host (mapeado do container).

### Como faço login no Docker?

Na primeira execução:
1. Não use `--headless`
2. Ou copie `cookies.json` existente para o diretório

## 📊 Estatísticas e Verificação

### Como vejo estatísticas?

```bash
# Modo nativo
python main.py --stats

# Com Docker
docker-compose --profile stats up

# Ou via Makefile
make stats
```

### Como verifico integridade dos arquivos?

```bash
python main.py --verify
```

Isso verifica:
- ✅ Arquivo existe no disco
- ✅ Hash SHA-256 corresponde
- ❌ Arquivo corrompido ou deletado

### Posso exportar estatísticas?

Sim, o database é SQLite padrão:

```bash
# Conecta ao banco
sqlite3 download_index.db

# Query exemplo
sqlite> SELECT course_name, COUNT(*), SUM(file_size)
        FROM downloads
        GROUP BY course_name;
```

## 🔒 Segurança e Privacidade

### Meus dados estão seguros?

**Armazenamento local:**
- Cookies: `cookies.json` (texto plano - proteja com `chmod 600`)
- Database: `download_index.db` (SQLite local)
- Nenhum dado enviado para terceiros

**Recomendações:**
```bash
# Proteger cookies
chmod 600 cookies.json

# Proteger downloads
chmod -R 700 ~/Downloads/Cursos
```

### Posso criptografar os cookies?

Planejado para v2.1. Enquanto isso:

```bash
# Use encfs ou similar
encfs ~/cookies_encrypted cookies_plaintext
cp cookies.json cookies_plaintext/
fusermount -u cookies_plaintext
```

### O projeto coleta telemetria?

**Não.** Zero telemetria. Todo processamento é 100% local.

## 🚀 Performance

### Qual a velocidade típica?

Depende de:
- Sua conexão (principal limitador)
- Workers configurados
- Modo async vs sync

**Benchmarks típicos:**
- 100 Mbps: ~10-12 MB/s
- 8 workers: ~4-6 arquivos simultâneos
- 1h de vídeo 720p: ~3-5 minutos

### Vale a pena usar uvloop?

**Sim**, em macOS/Linux ganha ~30-40% de velocidade async.

Já está habilitado automaticamente se disponível.

### HF Run Job melhora performance?

**Não.** Veja discussão completa na issue ou documentação.

TL;DR: O gargalo é rede, não CPU. HF Run Job não ajuda.

## 🤝 Contribuição e Suporte

### Como reporto bugs?

1. Abra uma [issue](https://github.com/prof-ramos/EstrategiaDownOF/issues)
2. Inclua: OS, Python version, logs, passos para reproduzir

### Como contribuo com código?

Veja [CONTRIBUTING.md](CONTRIBUTING.md)

### Encontrei uma vulnerabilidade de segurança

**NÃO** abra issue pública. Envie email para: prof.ramos@example.com

Veja [SECURITY.md](SECURITY.md)

---

**Não encontrou sua pergunta?**

- 📖 Leia o [README.md](README.md) completo
- 💬 Abra uma [Discussion](https://github.com/prof-ramos/EstrategiaDownOF/discussions)
- 📧 Email: prof.ramos@example.com
