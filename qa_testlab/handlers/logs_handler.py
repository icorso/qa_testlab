import logging
import sys
from logging import StreamHandler, basicConfig
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:

    def __new__(cls, log_errors_to_file: bool = False, file_path: str = None):
        stdout_handler = StreamHandler(stream=sys.stdout)
        handlers = [stdout_handler]

        if log_errors_to_file:
            if not file_path:
                raise AttributeError('file_path param is incorrect')
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                filename=file_path,
                mode='a',
                maxBytes=3*1024*1024,
                backupCount=2
            )
            file_handler.setLevel(logging.ERROR)  # пишет в файл записи с уровнем ERROR и выше
            handlers.append(file_handler)

        basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
            handlers=handlers
        )

        return logging.getLogger(__name__)
