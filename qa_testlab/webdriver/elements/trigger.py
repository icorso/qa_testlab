import allure

from qa_testlab.webdriver.page_objects import WebElement


class Trigger(WebElement):
    """
    Класс представляющий элемент веб-интерфейса Trigger / Checkbox
    """
    def is_checked(self):
        if self.get_attribute('value') == 'true' or self.get_attribute('checked') == 'true':
            return True
        return False

    @allure.step("Устанавливает значение переключателя {state}")
    def set_state(self, state: bool):
        if self.is_checked() != state:
            self.click()

    @allure.step("Проверяет значение переключателя = {state} для {0}")
    def has_state(self, state: bool):
        assert self.is_checked() == state, \
            f'Значение переключателя = {self.is_checked()} не соответствует ожидаемому {state}'
