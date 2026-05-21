import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "trading_bot", log_file: str = "trading_bot.log") -> logging.Logger:
    """
    Sets up a logger that writes to both a rotating log file (DEBUG+)
    and the console (INFO+).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # avoid duplicate handlers on re-import

    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", log_file)

    # --- File handler (DEBUG and above) ---
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
