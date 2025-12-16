"""
Configuração centralizada de logging para o projeto.

Uso:
    from src.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Mensagem", extra={"chats": 100})
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Retorna um logger configurado.

    Args:
        name: Nome do logger (geralmente __name__).
        level: Nível de log (DEBUG, INFO, WARNING, ERROR). Default: INFO ou LOG_LEVEL env.
        log_file: Caminho para arquivo de log. Se None, só stdout.

    Returns:
        Logger configurado.
    """
    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados
    if logger.handlers:
        return logger

    # Determina nível
    log_level_str = level or os.getenv("LOG_LEVEL") or "INFO"
    logger.setLevel(getattr(logging, log_level_str.upper(), logging.INFO))

    # Formato estruturado
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo (opcional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_run_logger(run_name: str = "run") -> logging.Logger:
    """
    Cria logger para uma execução específica com arquivo datado.

    Args:
        run_name: Nome da execução (ex: 'batch_analysis', 'etl').

    Returns:
        Logger com arquivo em logs/{run_name}_{date}.log
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/{run_name}_{timestamp}.log"
    return get_logger(f"run.{run_name}", log_file=log_file)


# Logger padrão para importação rápida
default_logger = get_logger("projeto_sdr")
