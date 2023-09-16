import json
import time
from time import sleep

import allure
import selenium.webdriver.support.expected_conditions as ec
from PIL import Image
from allure_commons.types import AttachmentType
from pixelmatch.contrib.PIL import pixelmatch
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

from qa_testlab import settings
from qa_testlab.settings import logger
from qa_testlab.webdriver.decorators import no_wait
from qa_testlab.webdriver.driver import get_driver
from qa_testlab.webdriver.expected_conditions import element_items_not_empty, element_text_not_empty


class WebHandler:
    """
    Класс с методами взаимодействия с любыми веб-страницами
    """

    def __init__(self, driver=None):
        self.driver = driver if driver else get_driver()

    @no_wait
    @allure.step("Ожидает исчезновение элемента '{web_element}' в течение {timeout} сек.")
    def waits_for_element_to_disappear(self, web_element, timeout=settings.implicit_wait):
        if web_element:
            try:
                WebDriverWait(self.driver, timeout).until(ec.invisibility_of_element(web_element))
            except (TimeoutException, StaleElementReferenceException):
                assert not TimeoutException, f'Элемент {web_element.name} всё еще присутствует ' \
                                             f'на странице {self.driver.current_url}'

    @allure.step("Ожидает появление элемента '{1}'")
    def waits_for_element_to_display(self, web_element, timeout=None):
        timeout = timeout if timeout else self.driver.timeouts.implicit_wait
        try:
            WebDriverWait(self.driver, timeout).until(ec.visibility_of(web_element))
        except (TimeoutException, AttributeError):
            name = f'- название: {web_element.name}\n' if web_element else ''
            assert False, f'Элемент не отобразился на странице в течение {timeout} секунд:\n{name}' \
                          f'- url: {self.driver.current_url}'
        except NoSuchElementException:
            assert False, f'Элемент отсутствует на странице {self.driver.current_url}'

    @allure.step("Ожидает появление не пустого списка {items_attribute} для элемента {element}")
    def waits_for_not_empty_elements_list(self, element, items_attribute='items', timeout=settings.implicit_wait):
        try:
            return WebDriverWait(self.driver, timeout).until(element_items_not_empty(element, items_attribute))
        except TimeoutException:
            raise TimeoutException(f'Элемент {element.name} содержит пустой список {items_attribute}')

    @allure.step("Ожидает '{timeout}' сек.")
    def waits_for(self, timeout=1.0):
        sleep(timeout)

    @allure.step("Перегружает текущую страницу")
    def reloads_page(self):
        self.driver.refresh()

    @allure.step("Перемещает элемент {source} к {target}")
    def drags_and_drops_to_element(self, source, target):
        """
        Перемещает элемент к указанному элементу
        Args:
            source (WebElement): элемент, который перемещается
            target (WebElement) элемент, к которому перемещается исходный
        """
        ActionChains(self.driver).drag_and_drop(source, target).perform()

    @allure.step('Перемещает курсор к координатам x={x} и y={y}')
    def move_by_offset(self, x, y):
        ActionChains(self.driver).move_by_offset(x, y).perform()

    @allure.step('Создаёт скриншот элемента "{element}"')
    def makes_screenshot(self, element, location=None, filename=None):
        """
        Создаёт скриншот указанного элемента
        Args:
            element (WebElement): элемент на странице
            location (str): папка в которой будет сохранён скриншот
            filename (str): название файла (с расширением)

        Returns: str полный путь к созданному скриншоту
        """
        element.location_once_scrolled_into_view()
        filename = filename if filename else \
            element.name.lower().replace(' ', '_').replace('"', '') + '_' + str(int(time.time())) + '.png'
        location = location if location else settings.temp_dir
        screenshot = f'{location}/{filename}'
        assert element.screenshot(screenshot), \
            f'Ошибка при создании скриншота. Возможно указан некорректный путь к файлу {screenshot}'
        return screenshot

    @allure.step("Сравнивает скриншоты {original_file} и {expected_file}")
    def compares_images(self, original_file, expected_file, threshold=0.1):
        """
        Сравнивает две картинки и создаёт diff в случае отличий
        Args:
            original_file: str путь к оригинальной картинки
            expected_file: str путь к эталонной картинке
            threshold: float 0..1 значение чувствительности, чем меньше значение, тем более чувствительное сравнение
        """
        original = Image.open(str(original_file))
        expected = Image.open(str(expected_file))
        diff = Image.new("RGBA", original.size)

        mismatch_pixels = pixelmatch(img1=original, img2=expected, output=diff, includeAA=False, threshold=threshold)
        expected_pixels = expected.size[0] * expected.size[1]
        mismatch_percentage = (mismatch_pixels / expected_pixels) * 100

        return mismatch_pixels, round(mismatch_percentage, 2), diff

    @allure.step('Сравнивает скриншоты "{elements_to_compare}"')
    def compares_element_with_screenshot(self, elements_to_compare: list):
        """
        Сравнивает скриншоты элементов с эталонными
        Args:
            elements_to_compare (dict): протокол (список словарей) передаваемых параметров для сравнения
            [
                {
                    "element": 'web_element',
                    "image": 'path/to/a.png' without root_dir_path,
                    "tolerance": float,
                    "exclude": [(By.XPATH, '//div')]
                }
            ], где element: HtmlElement элемент на странице который нужно сравнить с эталоном (обязательный)
               image: str путь к файлу эталонного скриншота (обязательный)
               exclude: list of tuples список локаторов, которые будут скрыты перед сравнением, например
                        (By.XPATH, './/div[@class='some_class']')
               tolerance: float допустимый процент отличий, значение по умолчанию 0.02
        """
        results = []
        for c in elements_to_compare:
            element = c.get('element') if 'element' in c.keys() else None
            expected_image = c.get('image') if 'image' in c.keys() else None
            tolerance = 0.02 if 'tolerance' not in c.keys() else float(c.get('tolerance'))
            exclude = c.get('exclude') if 'exclude' in c.keys() else None
            # проверка протокола
            assert 0.01 <= tolerance < 100, 'Допустимое значение tolerance >= 0.01 и <= 100.0'
            assert element, 'Пропущен обязательный параметр "element"'
            assert expected_image, 'Пропущен обязательный параметр "image"'
            expected_image = settings.root_dir / expected_image

            if exclude:  # исключает элементы перед снятием скриншота
                for locator in exclude:
                    for e in element.find_elements(*locator):
                        self.driver.execute_script("arguments[0].style.visibility='hidden'", e)
                sleep(1)  # иногда не успевает удалить несколько элементов

            original_image = self.makes_screenshot(element)
            original_filename = str(original_image).split('/')[-1]
            expected_filename = str(expected_image).split('/')[-1]
            diff_filename = original_filename.replace('.png', '_diff.png')
            diff_image = original_image.replace(original_filename, diff_filename)
            current_result = {'element': element.name, 'expected': expected_filename, 'original': original_filename,
                              'tolerance': f'допустимый процент отличий {tolerance}%'}

            with open(original_image, 'rb') as f:
                allure.attach(bytearray(f.read()), name=original_filename + ' (actual)',
                              attachment_type=AttachmentType.PNG)
            with open(expected_image, 'rb') as f:
                allure.attach(bytearray(f.read()), name=expected_filename + ' (expected)',
                              attachment_type=AttachmentType.PNG)

            try:
                comparison_data = self.compares_images(original_image, expected_image)
            except ValueError as e:  # добавляет ошибку в result и переходит к следующему элементу
                current_result.update(
                    {'result': str(type(e)(str(e) + '\nРазрешение сравниваемых скриншотов неодинаковое.'))})
                results.append(current_result)
                continue

            mismatch_pixels = comparison_data[0]
            mismatch_percentage = comparison_data[1]
            diff = comparison_data[2]

            if mismatch_pixels != 0:  # логирует сообщение о найденных отличиях, если они есть
                message = f'Оригинальный скриншот \'{expected_filename}\' отличается на {mismatch_percentage}% ' \
                          f'({str(mismatch_pixels)} pixels)'
                logger.info(message)

                if mismatch_percentage > tolerance:  # если найденные отличия больше допустимого процента, то
                    diff.save(diff_image)  # сохраняет снимок отличий и добавляет сообщение в result
                    with open(diff_image, 'rb') as f:
                        allure.attach(bytearray(f.read()), name=diff_filename, attachment_type=AttachmentType.PNG)
                    current_result.update({'result': message})
                    results.append(current_result)  # добавляет проверку элемента в словарь общих результатов проверки

        failures_formatted = json.dumps(results, ensure_ascii=False, indent=2)
        assert results == [], f'Обнаружены несоответствия в следующих скриншотах:\n{failures_formatted}'
