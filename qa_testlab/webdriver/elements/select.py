import allure
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

from qa_testlab.webdriver.driver import get_driver
from qa_testlab.webdriver.page_objects import WebElement


class Select(WebElement):
    """
    Класс представляющий элемент веб-интерфейса Select (выпадающий список)
    """

    @property
    def elements(self):
        return self.find_elements(By.CSS_SELECTOR, 'div')

    def get(self, value):
        elements = self.elements
        element = [e for e in elements if e.text == str(value)]
        if len(element) > 0:
            return element[0]
        assert False, f'Пункт "{value}" не найден в списке {[e.text for e in elements]}'

    @allure.step("Выбирает пункт {value} из списка '{0}'")
    def select_by_value(self, value):
        self.click(timeout=0.5)
        list_item = self.get(value)
        ActionChains(get_driver()).move_to_element(list_item).perform()
        list_item.click()
