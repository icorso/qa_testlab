import os
from pathlib import Path

from qa_testlab.handlers.logs_handler import Logger

# веб сервисы
scheme = 'http://'
host = 'localhost'
port = 80
url = f'{scheme}{host}:{port}'
rest_port = 55555
rest_url = f'{scheme}{host}:{rest_port}'

# ssh доступ
ssh_login = 'root'
ssh_password = 'password'
ssh_port = 22

root_dir = Path(__file__).parent.parent.resolve()
temp_dir = root_dir / '.tmp'

# настройки браузера
implicit_wait = float(os.getenv('implicit_wait', 0.1))
short_implicit_wait = float(os.getenv('short_implicit_wait', 2))
element_wait = float(os.getenv('element_wait', 3))
browser_name = 'chrome'
browser_version = None
local_driver_cache_valid_range = 7  # время жизни кэша локального драйвера в днях
grid_url = 'http://192.168.4.79:4444/wd/hub'
local_run = os.getenv('local_run', 'False').lower() in ('true', '1')
headless = os.getenv('headless', 'True').lower() in ('true', '1')

logger = Logger()
