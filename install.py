import os
import subprocess
import sys

from config import BaseConfig

# Установка зависимостей
subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
)

# Создание директорий
for local_directory in (
    BaseConfig.DATA_DIR,
    BaseConfig.MODELS_DIR,
    BaseConfig.LOGS_DIR,
):
    if not os.path.exists(local_directory):
        os.mkdir(local_directory, 0o755)