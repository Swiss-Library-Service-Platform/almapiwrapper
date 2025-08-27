# Configuration des logs
from typing import Optional
import logging
import sys
import os


def config_log(file_name: Optional[str] = "") -> None:
    """Set the log configuration for the entire process

    The logs are written in a file located in the log folder. If the folder
    doesn't exist, it is created. The log file is named "log_<file_name>.txt".
    If no file_name is provided, the log file is named "log.txt".

    :param file_name: name of the log file

    :return: None
    """

    # Create the log folder if it doesn't exist
    if not os.path.isdir('./log'):
        os.mkdir('./log')

    message_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_file_name = f'log/log{"" if len(file_name) == 0 else "_"}{file_name}.txt'
    logging.basicConfig(format=message_format,
                        level=logging.INFO,
                        handlers=[logging.FileHandler(log_file_name),
                                  logging.StreamHandler(sys.stdout)])


if __name__ == "__main__":
    pass
