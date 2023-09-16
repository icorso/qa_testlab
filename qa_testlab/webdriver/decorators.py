from functools import wraps

from qa_testlab import settings
from qa_testlab.webdriver.driver import get_driver


def no_wait(func):
    @wraps(func)
    def without_wait(*args, **kwargs):
        try:
            get_driver().implicitly_wait(0)
            return func(*args, **kwargs)
        finally:
            get_driver().implicitly_wait(settings.implicit_wait)
    return without_wait
