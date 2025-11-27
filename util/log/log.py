import logging
import os
from datetime import datetime


class Log:
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is not None:
            return cls._logger

        logger = logging.getLogger("server")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            GREEN = "\033[92m"
            RESET = "\033[0m"

            # 콘솔용: 초록색 levelname
            console_formatter = logging.Formatter(
                f'{GREEN}%(levelname)s{RESET}(%(asctime)s) : %(filename)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 파일용: 색 없음
            file_formatter = logging.Formatter(
                '%(levelname)s(%(asctime)s) : %(filename)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(console_formatter)

            log_dir = os.path.join(os.getcwd(), "logs")
            os.makedirs(log_dir, exist_ok=True)

            date_str = datetime.now().strftime("%Y%m%d")
            log_path = os.path.join(log_dir, f"{date_str}_log.log")

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(file_formatter)

            logger.addHandler(stream_handler)
            logger.addHandler(file_handler)

        cls._logger = logger
        return logger
