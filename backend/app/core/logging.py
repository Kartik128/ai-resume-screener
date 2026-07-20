import sys
import logging
from loguru import logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Standard logging interceptor to redirect Python standard logging calls to loguru.
    """
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configure structured logging for FastAPI application.
    """
    # Remove default handlers
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Intercept standard library loggers
    for log_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "sqlalchemy.engine"):
        mod_logger = logging.getLogger(log_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    logger.remove()
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        level="DEBUG" if settings.DEBUG else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
