import inspect
from collections import UserList
from time import sleep
from types import MethodType
from typing import TypeVar

import allure
from selenium.common.exceptions import NoSuchElementException, TimeoutException, InvalidElementStateException
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement as WebDriverElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

import qa_testlab.settings as settings
from qa_testlab.webdriver.decorators import no_wait
from qa_testlab.webdriver.driver import get_driver
from qa_testlab.webdriver.expected_conditions import element_contains_text, element_has_text


def is_element_present(self, element_name, timeout=0):
    get_driver().implicitly_wait(timeout)
    try:
        element = getattr(self, element_name)
        if isinstance(element, list):
            return all(e.is_displayed() for e in element)
        return element.is_displayed()
    except (AttributeError, NoSuchElementException):
        return False
    finally:
        get_driver().implicitly_wait(settings.implicit_wait)


class WebElement(WebDriverElement):
    _name = ""
    T = TypeVar("T")
    N = TypeVar("N", int, float)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name

    @property
    def int(self):
        return int(self.text.replace(' ', ''))

    @property
    def float(self):
        return float(self.text.replace(' ', ''))

    @allure.step("Нажимает элемент {0}")
    def click(self, timeout: float = 0) -> None:
        """
        Нажимает на элемент
        Args:
            timeout (float): ожидание после нажатия (в секундах)
        Returns: None
        """
        WebDriverWait(get_driver(), settings.implicit_wait).until(ec.element_to_be_clickable(self))
        super().click()
        if timeout > 0:
            sleep(timeout)

    @allure.step("Двойное нажатие на элемент {0}")
    def double_click(self) -> None:
        """
        Двойное нажатие на элемент
        Returns: None
        """
        WebDriverWait(get_driver(), settings.implicit_wait).until(ec.element_to_be_clickable(self))
        ActionChains(get_driver()).double_click(self).perform()

    @allure.step("Вводит текст {1} в {0}")
    def send_keys(self, value, clear: bool = True) -> None:
        """
        Вводит текст в поле
        Args:
            value: значение, которое нужно ввести в поле
            clear (bool): очищать поле пере вводом
        Returns: None
        """
        for i in range(10):
            try:
                if clear:
                    if hasattr(self, 'clear') and inspect.ismethod(getattr(self, 'clear')):
                        self.clear()
                    else:
                        super().clear()
                super().send_keys(value)
                break
            except InvalidElementStateException:
                sleep(0.2)

    @allure.step("Перемещается к элементу {0}")
    def location_once_scrolled_into_view(self):
        get_driver().execute_script('arguments[0].scrollIntoView({block: "center", inline: "center"})', self)

    @allure.step('Смещает элемент {0} на x="{x_offset}", y="{y_offset}" позиций')
    def drag_and_drop_by_offset(self, x_offset, y_offset):
        ActionChains(get_driver()).drag_and_drop_by_offset(self, x_offset, y_offset).perform()

    @allure.step('Перемещает курсор к элементу {0}')
    def move_to_element(self):
        ActionChains(get_driver()).move_to_element(self).perform()

    @allure.step('Перемещает и отпускает курсор от текущего положения к элементу {0}')
    def click_and_hold(self):
        ActionChains(get_driver()).click_and_hold().release(self).perform()

    @no_wait
    @allure.step("Текст элемента '{0}' соответствует '{1}'")
    def has_text(self, *text: str, timeout=None):
        timeout = timeout if timeout else settings.short_implicit_wait
        try:
            WebDriverWait(self.parent, timeout).until(element_has_text(self, *text))
        except TimeoutException:
            assert False, f'Ожидаемый текст "{text}" не соответствует тексту "{self.text}" элемента "{self.name}"'

    @no_wait
    @allure.step("Текст '{1}' содержится в тексте элемента '{0}'")
    def contains_text(self, *text: str, timeout=None):
        timeout = timeout if timeout else settings.short_implicit_wait
        try:
            WebDriverWait(self.parent, timeout).until(element_contains_text(self, *text))
        except TimeoutException:
            assert False, f'Ожидаемый текст "{text}" не содержится в тексте "{self.text}" элемента "{self.name}"'

    @allure.step("Элемент '{0}' содержит значение атрибута {attribute} = {value}")
    def contains_attribute_value(self, value, attribute: str = 'text'):
        actual_attribute_value = self.get_attribute(attribute)
        assert value in actual_attribute_value, \
            f'Элемент "{self.name}" не содержит значение "{value}" атрибута {attribute}: {actual_attribute_value} '

    @allure.step("Проверяет состояние is_enabled={is_enabled} элемента {0}")
    def has_state(self, is_enabled: bool):
        assert self.is_enabled() == is_enabled, f'Свойство is_enabled не соответствует ожидаемому "{is_enabled}"'

    @allure.step("Проверяет наличие вертикальной прокрутки у элемента {0}")
    def is_scrollable(self):
        scroll_height = int(self.get_attribute("scrollHeight"))
        offset_height = int(self.get_attribute("offsetHeight"))
        return bool(scroll_height > offset_height)


class WebElementsList(UserList):
    def __init__(self, iterable):
        self._name = ""
        self.iterable = iterable
        super().__init__(iterable)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def items(self):
        return self.iterable

    def __str__(self):
        return self._name

    def __repr__(self):
        return self._name

    def has_size(self, size: int, attribute: str=None):
        """
        Сравнивает количество элементов в списке
        Args:
            size (int): ожидаемое количество элементов в списке
            attribute: атрибут класса из списка iterable
        """
        actual_size = len(self.iterable) if not attribute \
            else len([i for i in self.iterable if getattr(i, attribute) is not None])
        assert actual_size == size, f'Не совпадает количество элементов в списке: {actual_size} != {size}'

    @allure.step("Элемент '{0}' содержит значения атрибута {attribute} = {values}, включая порядок = {in_any_order}")
    def has_values(self, values: list, in_any_order=True, attribute='text', attribute_type='tag'):
        """
        Проверяет значения списка
        Args:
            values (list): список ожидаемых значений
            in_any_order (bool): учитывать порядок
            attribute (str): аттрибут элемента (тега) для значений
            attribute_type (str): тип аттрибут. Допустимые значения tag или class. Например, если нужно проверить
                                  значения для списка HtmlElements представляющего html тег с атрибутом href, то нужно
                                  передать attribute='href' и attribute_type='tag'. Если список HtmlElements, у
                                  которого ui_type определён каким-либо классом с атрибутом title, то нужно передать
                                  attribute='title' и attribute_type='class'.
        """
        types = ['tag', 'class']
        assert attribute_type.lower() in types, f'Неверное значение attribute_type. Допустимые типы: {types}'
        if attribute == 'text' and attribute_type=='tag':
            original_values = [x.text for x in self.iterable]
        else:
            original_values = [x.get_attribute(attribute) if attribute_type.lower() == 'tag'
                else getattr(x, attribute).text for x in self.iterable]
        expected_values = list(values)

        if in_any_order:
            original_values = sorted(original_values)
            expected_values = sorted(expected_values)

        assert original_values == expected_values, \
            f'Значения:\n{original_values}\n не совпадают с ожидаемыми:\n{expected_values}'

    @allure.step("Значения элемента '{0}' не содержат текст '{text}'")
    def has_no_text(self, text):
        assert text not in [e.text for e in self.iterable], f'"{self.name}" не должен содержать текст "{text}"'

    @allure.step("Значения элемента '{0}' содержат текст '{text}'")
    def has_text(self, text):
        assert text in [e.text for e in self.iterable], f'"{self.name}" не содержит текст "{text}"'


class HtmlPage(object):
    def __init__(self, driver=None, url=None):
        if url:
            self.url = url
        self.__driver = driver if driver else get_driver()
        self.is_element_present = MethodType(is_element_present, self)

    @property
    def _driver(self):
        if self.__driver:
            return self.__driver
        return get_driver()

    @allure.step("Открывает url")
    def open(self):
        if not self.url:
            raise Exception('Параметр url не задан')
        self.__driver.get(self.url)

    def find_element(self, *args):
        return self.__driver.find_element(*args)

    def find_elements(self, *args):
        return self.__driver.find_elements(*args)

    def implicitly_wait(self, *args):
        return self.__driver.implicitly_wait(*args)


class HtmlElement(object):
    def __init__(self, name: str, by: str, value,
                 ui_type = WebElement,
                 use_context: bool = True,
                 shadow_selector: tuple = None,  # допустимые By.ID By.CLASS_NAME By.NAME, пример (By.CLASS_NAME, 'Field')
                 *args,
                 **kwargs):
        self.name = name
        self.by = by
        self.value = value
        self.ui_type = ui_type
        self.use_context = use_context
        self.init_args = args
        self.init_kwargs = kwargs
        self._shadow_selector = shadow_selector
        self._target_element = None
        self._context = None
        self._validate_params()

    @property
    def _driver(self):
        return get_driver()

    def _validate_params(self):
        if not self.by:
            if issubclass(self.ui_type, WebElement):
                raise Exception('Логический контейнер не должен быть WebElement')
        else:
            if not issubclass(self.ui_type, WebElement):
                raise Exception('UI типы должны наследоваться от WebElement')

    def __get__(self, obj, *args):
        self._context = obj
        self._search_element()
        if self._target_element:
            self._target_element.name = self.name
        return self._target_element

    def _search_element(self, timeout=settings.implicit_wait):
        try:
            search_context = self._context if self.use_context else self._driver
            web_element = search_context.find_element(self.by, self.value)
            self._target_element = web_element

            if self._shadow_selector:
                self._target_element = web_element.shadow_root.find_element(*self._shadow_selector)

            self._target_element.__class__ = self.ui_type
        except (NoSuchElementException, TimeoutException):
            self._target_element = None
            return None
        self._target_element.is_element_present = MethodType(is_element_present, self._target_element)

        if len(self.init_args) or len(self.init_kwargs) > 0:
            self._target_element.__init__(*self.init_args, **self.init_kwargs)


class HtmlElements(HtmlElement):
    @property
    def _driver(self):
        return get_driver()

    def _validate_params(self):
        if not issubclass(self.ui_type, WebElement):
            raise Exception('HtmlElements применим только для WebElement')

    def _search_element(self, timeout=settings.implicit_wait):
        search_context = self._context if self.use_context else self._driver
        self._target_element = WebElementsList(search_context.find_elements(self.by, self.value))
        for index, item in enumerate(self._target_element):
            item.__class__ = self.ui_type
            item.name = f'{self.name} - элемент #{index}'
            item.is_element_present = MethodType(is_element_present, item)
            item.implicitly_wait = self._driver.implicitly_wait
