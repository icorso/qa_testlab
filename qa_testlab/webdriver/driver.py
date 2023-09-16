import json
import os

import allure
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

import qa_testlab.settings as settings
from webdriver_manager.core.driver_cache import DriverCacheManager

_driver_instance = None


def init_driver(browser_name,
                browser_version=None,
                is_run_locally=False,
                headless=True,
                implicit_wait=settings.implicit_wait,
                *args, **kwargs):
    driver_class = webdriver.Remote

    if browser_name == 'edge':
        options = webdriver.EdgeOptions()
        options.set_capability("ms:edgeOptions", {"args": []})
        if is_run_locally:
            driver_class = webdriver.Edge
        kwargs.update({'options': options})

    if browser_name == 'firefox':
        options = webdriver.FirefoxOptions()
        options.headless = headless

        if is_run_locally:
            os.environ['WDM_LOCAL'] = '1'
            os.environ['WDM_SSL_VERIFY'] = '0'
            driver_class = webdriver.Firefox
            kwargs.update({'executable_path': GeckoDriverManager().install()})
        else:
            options.set_capability('browserName', browser_name)
            if browser_version:
                options.set_capability('browserVersion', browser_version)
            options.set_capability('acceptInsecureCerts', True)
            options.set_capability('moz:debuggerAddress', True)
            options.set_capability('moz:firefoxOptions', {"args": [f"{'-headless' if headless else None}"]})
        kwargs.update({'options': options})

    if browser_name == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument('allow-elevated-browser')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--log-level=0")
        # available capabilities 'driver': 'ALL', 'performance': 'ALL'
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

        if headless:
            options.add_argument("headless")

        if is_run_locally:
            os.environ['WDM_LOCAL'] = '1'
            os.environ['WDM_SSL_VERIFY'] = '0'
            driver_class = webdriver.Chrome
            kwargs.update({'service': Service(
                ChromeDriverManager(
                    cache_manager=DriverCacheManager(valid_range=settings.local_driver_cache_valid_range)
                ).install()
            )})
        else:
            options.set_capability('browserName', browser_name)
            if browser_version:
                options.set_capability('browserVersion', browser_version)

        kwargs.update({'options': options})

    if not is_run_locally:
        kwargs.update({"command_executor": settings.grid_url})

    class WebdriverWrapper(driver_class):
        def __init__(self, implicit_wait=implicit_wait, *args, **kwargs):
            self._implicit_wait = implicit_wait
            super(WebdriverWrapper, self).__init__(*args, **kwargs)
            super(WebdriverWrapper, self).implicitly_wait(self._implicit_wait)

        def execute_cdp_cmd(self, cmd, params=None):
            if params is None:
                params = {}
            resource = "/session/%s/chromium/send_command_and_get_result" % self.session_id
            url = self.command_executor._url + resource
            body = json.dumps({'cmd': cmd, 'params': params})
            response = self.command_executor._request('POST', url, body)
            return response.get('value')

        @allure.step("Перегружает текущую страницу")
        def refresh(self):
            super().refresh()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()

    return WebdriverWrapper(*args, **kwargs)


def get_driver():
    global _driver_instance
    if not _driver_instance:
        _driver_instance = init_driver(
            browser_name=settings.browser_name,
            browser_version=settings.browser_version,
            is_run_locally=settings.local_run,
            headless=settings.headless,
            implicit_wait=settings.implicit_wait
        )
        _driver_instance.maximize_window()
        _driver_instance.set_window_size(1920, 1080)
        _driver_instance.implicitly_wait(settings.implicit_wait)
    return _driver_instance


def get_driver_no_init():
    return _driver_instance


def close_driver():
    global _driver_instance
    if _driver_instance:
        _driver_instance.quit()
        _driver_instance = None

class WebdriverContext:
    def __init__(self, driver=None):
        self.driver = driver if driver else get_driver()

    def __enter__(self):
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        close_driver()
