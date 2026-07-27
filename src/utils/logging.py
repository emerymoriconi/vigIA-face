import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = False,
    filename: str = "logs/app.log",
    backup_count: int = 30
) -> None:
    """Configura logger raiz."""
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    
    if log_to_file:
        # Garante que o diretório de logs exista
        log_dir = os.path.dirname(filename)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        # Rotação diária à meia-noite, mantendo 'backup_count' dias
        file_handler = TimedRotatingFileHandler(
            filename, 
            when="midnight", 
            interval=1, 
            backupCount=backup_count, 
            encoding="utf-8"
        )
        # Formato de data customizado para o sufixo do arquivo rotacionado
        file_handler.suffix = "%Y-%m-%d"
        handlers.append(file_handler)

    # Configuração global do formato do log (Padrão PlatePi)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
