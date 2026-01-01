"""Sistema de logging estruturado para EstrategiaDownOF."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    """Formatter que adiciona cores aos logs no console."""

    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.CYAN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
    }

    ICONS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
    }

    def format(self, record: logging.LogRecord) -> str:
        """Formata o log com cores e ícones."""
        # Adiciona cor baseada no nível
        color = self.COLORS.get(record.levelname, '')
        icon = self.ICONS.get(record.levelname, '')

        # Formata a mensagem
        record.levelname = f"{color}{icon} {record.levelname}{Style.RESET_ALL}"
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


def setup_logger(
    name: str = "estrategia_downloader",
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True,
) -> logging.Logger:
    """Configura o logger da aplicação com suporte a arquivo e console.

    Args:
        name: Nome do logger.
        log_level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Caminho para arquivo de log (opcional).
        console: Se True, loga também no console.

    Returns:
        Logger configurado.

    Example:
        >>> logger = setup_logger("meu_app", log_level="DEBUG", log_file=Path("app.log"))
        >>> logger.info("Aplicação iniciada")
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove handlers existentes para evitar duplicação
    logger.handlers.clear()

    # Formato para arquivo (mais detalhado)
    file_format = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Formato para console (mais limpo)
    console_format = ColoredFormatter(
        fmt='%(levelname)s %(message)s',
        datefmt='%H:%M:%S'
    )

    # Handler de console
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_format)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        logger.addHandler(console_handler)

    # Handler de arquivo
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_format)
        file_handler.setLevel(logging.DEBUG)  # Arquivo sempre tem tudo
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "estrategia_downloader") -> logging.Logger:
    """Retorna o logger da aplicação (já configurado).

    Args:
        name: Nome do logger.

    Returns:
        Logger existente ou cria um novo se não existir.

    Example:
        >>> logger = get_logger()
        >>> logger.info("Baixando arquivo...")
    """
    logger = logging.getLogger(name)

    # Se não tem handlers, configura com defaults
    if not logger.handlers:
        return setup_logger(name)

    return logger


# Logger global para uso rápido
logger = get_logger()


# Funções de conveniência (compatibilidade com código existente)
def log_debug(msg: str) -> None:
    """Log de debug."""
    logger.debug(msg)


def log_info(msg: str) -> None:
    """Log informacional."""
    logger.info(msg)


def log_success(msg: str) -> None:
    """Log de sucesso (INFO com emoji)."""
    logger.info(f"✓ {msg}")


def log_warn(msg: str) -> None:
    """Log de aviso."""
    logger.warning(msg)


def log_error(msg: str) -> None:
    """Log de erro."""
    logger.error(msg)


def log_critical(msg: str) -> None:
    """Log crítico."""
    logger.critical(msg)


# Context manager para logging temporário de arquivo
class LogToFile:
    """Context manager para logging temporário em arquivo.

    Example:
        >>> with LogToFile("debug.log", level="DEBUG"):
        ...     logger.debug("Isso vai para debug.log")
    """

    def __init__(self, log_file: str | Path, level: str = "DEBUG"):
        """Inicializa o context manager.

        Args:
            log_file: Caminho do arquivo de log.
            level: Nível de logging.
        """
        self.log_file = Path(log_file)
        self.level = level
        self.handler: Optional[logging.FileHandler] = None

    def __enter__(self):
        """Adiciona handler de arquivo."""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.handler.setFormatter(formatter)
        self.handler.setLevel(getattr(logging, self.level.upper()))

        logger.addHandler(self.handler)
        return logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Remove handler de arquivo."""
        if self.handler:
            logger.removeHandler(self.handler)
            self.handler.close()
