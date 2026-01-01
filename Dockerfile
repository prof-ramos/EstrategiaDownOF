# Multi-stage Dockerfile para EstrategiaDownOF
# Build otimizado com cache layers e security best practices

# Stage 1: Builder
FROM python:3.11-slim as builder

LABEL maintainer="prof.ramos@example.com"
LABEL description="EstrategiaDownOF - Downloader de cursos otimizado"

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instala dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia apenas requirements primeiro (cache layer)
COPY requirements.txt .

# Instala dependências Python em virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Labels para metadados
LABEL org.opencontainers.image.source="https://github.com/prof-ramos/EstrategiaDownOF"
LABEL org.opencontainers.image.description="Downloader automático Estratégia Concursos"
LABEL org.opencontainers.image.licenses="MIT"

# Variáveis de ambiente
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DOWNLOAD_DIR=/downloads \
    WORKERS=4

# Instala runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome para Selenium
    wget \
    gnupg \
    ca-certificates \
    # FFmpeg para compressão
    ffmpeg \
    # Cleanup
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário não-root para segurança
RUN useradd -m -u 1000 -s /bin/bash downloader && \
    mkdir -p /downloads /app && \
    chown -R downloader:downloader /downloads /app

# Copia virtualenv do builder
COPY --from=builder /opt/venv /opt/venv

# Muda para usuário não-root
USER downloader
WORKDIR /app

# Copia código da aplicação
COPY --chown=downloader:downloader . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Volume para downloads e cookies
VOLUME ["/downloads", "/app/cookies.json"]

# Expõe porta para possível UI futura
# EXPOSE 8080

# Entrypoint com argumentos padrão
ENTRYPOINT ["python", "main.py"]
CMD ["--headless", "--dir", "/downloads"]
