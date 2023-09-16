from time import sleep

from selenium.webdriver.remote.webelement import WebElement


class elements_list_not_empty(object):
    def __init__(self, locator: tuple, pooling_timeout=0):
        self.locator = locator
        self.pooling_timeout = pooling_timeout / 1000

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        elements = driver.find_elements(*self.locator)
        if len(elements) > 0:
            return elements
        else:
            return False

class element_items_not_empty(object):
    def __init__(self, element, items_attribute, pooling_timeout=0):
        self.element = element
        self.items_attribute = items_attribute
        self.pooling_timeout = pooling_timeout / 1000

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        if len(getattr(self.element, self.items_attribute)) > 0:
            return getattr(self.element, self.items_attribute)
        else:
            return False

class element_text_not_empty(object):
    """
    Ожидание элемента с непустым текстом
    """
    def __init__(self, element: WebElement, pooling_timeout: float = 0):
        """
        Args:
            element: инициализированный экземпляр класса WebElement
            pooling_timeout: float время повторного опроса (в миллисекундах)
        """
        self.element = element
        self.pooling_timeout = pooling_timeout / 100

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        if self.element:
            if len(self.element.text) > 0:
                return True
        return False

class element_text_empty(object):
    """
    Ожидание элемента с пустым текстом
    """
    def __init__(self, element: WebElement, pooling_timeout: float = 0):
        """
        Args:
            element: инициализированный экземпляр класса WebElement
            pooling_timeout: float время повторного опроса (в миллисекундах)
        """
        self.element = element
        self.pooling_timeout = pooling_timeout / 100

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        if self.element:
            if len(self.element.text) == 0:
                return True
        return False

class element_contains_text(object):
    """
    Ожидание элемента содержащего текст (неполное совпадение одного из текстов)
    """
    def __init__(self, element: WebElement, *text, pooling_timeout: float = 0):
        """
        Args:
            element: инициализированный экземпляр класса WebElement
            text: tuple ожидаемый текст (один и более)
            pooling_timeout: float таймаут повторного опроса (в миллисекундах)
        """
        self.element = element
        self.text = text
        self.pooling_timeout = pooling_timeout / 1000

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        if self.element:
            if any(t in self.element.text for t in self.text):
                return True
        return False


class element_has_text(object):
    """
    Ожидание элемента с текстом (полное совпадение одного из текстов)
    """
    def __init__(self, element: WebElement, *text, pooling_timeout: float = 0):
        """
        Args:
            element: инициализированный экземпляр класса WebElement
            text: tuple ожидаемый текст
            pooling_timeout: float таймаут повторного опроса (в миллисекундах)
        """
        self.element = element
        self.text = text
        self.pooling_timeout = pooling_timeout / 1000

    def __call__(self, driver):
        sleep(self.pooling_timeout)
        if self.element:
            if any(self.element.text == t for t in self.text):
                return True
        return False
