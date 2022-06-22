# Configuration des logs
from typing import Optional
import logging
import sys


def config_log(file_name: Optional[str] = "") -> None:
    """
    Set the configuration for the entire process
    :param file_name: name of the log file
    :return: None
    """
    message_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_file_name = f'log/log{"" if len(file_name) == 0 else "_"}{file_name}.txt'
    logging.basicConfig(format=message_format,
                        level=logging.INFO,
                        handlers=[logging.FileHandler(log_file_name),
                                  logging.StreamHandler(sys.stdout)])
