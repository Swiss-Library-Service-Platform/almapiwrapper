# Configuration des logs
from typing import Optional
import logging
import sys
import os


def config_log(file_name: Optional[str] = "") -> None:
    """
    Configure application logging.

    This function initializes logging for the entire process. Log messages are written to a file, and
    the necessary directories are created automatically if they do not exist.

    - If ``file_name`` contains a path (e.g. ``logs/subdir/mylog``), all required directories are created.
    - If ``file_name`` is just a file name, the log file is created in the ``./log/`` directory.
    - If ``file_name`` is empty, the log file ``./log/log.txt`` is used.
    - The log file name is determined automatically from ``file_name``.
    - Log messages are also output to standard output (the console).

    :param file_name: Optional string containing the name of the log file (may include a relative or absolute path).

    :return: None
    """

    # Create the log folder if it doesn't exist
    log_dir = os.path.dirname(file_name)
    if log_dir:
        log_file_name = os.path.basename(file_name)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    else:
        if len(file_name) == 0:
            log_file_name = 'log.txt'
        else:
            log_file_name = file_name
        if not os.path.isdir('./log'):
            os.mkdir('./log')
            log_dir = './log'

    log_file_path = os.path.join(log_dir, log_file_name)
    message_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=message_format,
                        level=logging.INFO,
                        handlers=[logging.FileHandler(log_file_path),
                                  logging.StreamHandler(sys.stdout)])


if __name__ == "__main__":
    pass
