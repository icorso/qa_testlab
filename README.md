# qa-testlab

Фреймворк для автоматизированного тестирования веб приложений и REST API запросов

---
## Сборка

сборка с использованием **build** инструмента:

    pip install build
    python3 -m build --wheel

или **bdist_wheel**:

    python3 setup.py bdist_wheel

После сборки файл для установки доступен в папке dist:

    dist/qa_testlab-0.0.1-py3-none-any.whl

---
## Установка
Для установки нужно выполнить следующую команду:

      pip install qa_testlab-0.0.1-py3-none-any.whl

---
## Использование для тестирования веб-страниц
### Основные классы и их взаимодействие
Модуль qa_testlab.webdriver.page_objects содержит базовые классы.

**HtmlPage** - класс описывающий непосредственно веб-страницу.

**HtmlElement** - класс описывающий элемент на веб-странице.

**HtmlElements** - класс описывающий список элементов.

**WebElement** - наследуется от класса selenium.webdriver.remote.webelement.WebElement. Расширяет базовый класс 
свойством name и методами, декорированными @allure.step.

**WebElementsList** - по аналогии с WebElement содержит свойство name и ряд @allure.step методов, но наследуется от 
класса UserList.

По сути HtmlPage класс является контейнером, в котором хранятся элементы страницы описанные в виде HtmlElement / 
HtmlElements классов. Поиск элемента на странице происходит "лениво", т.е. инициализируется при обращении к атрибуту
экземпляра HtmlPage класса, например из теста. Результатом инициализации будет экземпляр класса WebElement / 
WebElementsList, и уже через их методы будет происходить взаимодействие с содержимым страницы (ввод текста, нажатие, 
проверки текста и значений атрибутов html-тега).

В сигнатуре класс HtmlElement / HtmlElements обязательными являются 3 параметра:
- **name** - наименование элемента (будет отображено в allure отчёте); 
- **by** - указывает по какому атрибуту производится поиск элемента (см. https://selenium-python.readthedocs.io/locating-elements.html) 
- **value** - значение селектора для поиска

необязательные параметры:
- **ui_type** (по умолчанию WebElement) - класс типа элемента, можно передать класс типизированных элементов (см. ниже)
или любые сложные блоки страницы унаследованных от WebElement класса.
- **use_context** (по умолчанию True) - контекст поиска веб-элемента. True - поиск осуществляется с уровня родительского 
элемента, False - верхнего уровня веб-страницы.  
- **shadow_selector** (по умолчанию None) - кортеж типа и значения (By.ID, 'id') селектора shadow_root элемента "теневого" 
DOM внутри основного (https://learn.javascript.ru/shadow-dom), корректные значения By: By.ID, By.CLASS_NAME, By.NAME
  
### Типизированные элементы интерфейса
Классы более сложных элементов веб-интерфейсов находятся в пакете qa_testlab.webdriver.elements 

Select - представление выпадающего списка

Table - представление таблицы

Trigger - представление элемента checkbox (переключатель)

Как было сказано выше, эти классы используются как значение параметра ui_type в HtmlElement / HtmlElements классах.

Пример использования страницы с элементами:
```
Файл login_page.py

from qa_testlab.webdriver.page_objects import HtmlElement, HtmlPage

class LoginPage(HtmlPage):
    username = HtmlElement('Поле "Имя пользователя"', By.CSS_SELECTOR, '[label="Имя пользователя"]', 
                            shadow_selector=(By.CLASS_NAME, 'Field'))
    password = HtmlElement('Поле "Пароль"', By.CSS_SELECTOR, '[label="Пароль"]',
                           shadow_selector=(By.CLASS_NAME, 'Field'))

Файл test_login.py

def test_login()
    login_page = LoginPage()
    login_page.username.send_keys('admin')
    ...   
```

Пример описания блоков элементов:
```
Файл login_page.py

from qa_testlab.webdriver.page_objects import HtmlElement, HtmlPage
from qa_testlab.webdriver.elements.select import Select

class TableConfigPanel(WebElement):
    datasources = HtmlElement('Список "Источник данных"', By.TAG_NAME, 'datasource-select',
                               shadow_selector=(By.CSS_SELECTOR, 'base-select'), ui_type=Select)

class TablePage(HtmlPage):
    table_config_panel = HtmlElement('Панель конфигурирования таблицы', By.CLASS_NAME, 'ConfigEditorPanel', 
                                      ui_type=TableConfigPanel)

Файл test_table_config.py

def test_table_datasource_select()
    table_page = TablePage()
    table_page.table_config_panel.datasources.select_by_value('данные за день')
    ...   

```

### Хендлеры
Хендлеры содержат классы и методы, которые позволяют взаимодействовать с разными системами: файловой, веб, REST API
и логирования.

- **FSHandler** из модуля qa_testlab.handlers.fs_handler содержит методы для взаимодействия с файловой системой, как 
локальной, так и удалённой (посредством SSH протокола). Для этого используется две имплементации файловой системы из 
библиотеки fsspec - fsspec.implementations.local.LocalFileSystem и fsspec.implementations.sftp.SFTPFileSystem.
Выбор типа используемой системы происходить автоматически, в зависимости от настроек (settings.host и settings.port) 
модуля qa_testlab.settings. Пример использования в качестве фикстуры:
```
    from qa_testlab.handlers.fs_handler import get_fsspec, FSHandler

    @pytest.fixture()
    def fs():
        fsspec = get_fsspec(settings.host, settings.ssh_port, settings.ssh_login, settings.ssh_password)
        return FSHandler(fsspec)
```

- **WebHandler** из модуля qa_testlab.handlers.web_handler содержит методы взаимодействия с элементами веб-страниц.
Для инициализации хендлера достаточно создать экземпляр класса без параметра. В качестве необязательного параметра
в экземпляр так же можно передать веб-драйвер.
```
    from qa_testlab.handlers.rest_api_hadler import RestfullApiClient
    
    @pytest.fixture()
    def user():
        return WebHandler()
```
- **RestfullApiClient** из модуля qa_testlab.handlers.rest_api_handler содержит клиента для доступа к REST API. 
Основной метод call_api с параметрами позволяет строить различные запросы к API и логировать их выполнение. В основе 
лежит библиотека requests. Результатом выполнения будет экземпляр класса requests.Response, который можно 
сериализовать в json. Все параметры (кроме метода и пути) передаются через параметр request_data в виде словаря. 
Параметры далее передаются в метод requests.Session().request() (более подробно какие параметры он принимает по ссылке 
https://requests.readthedocs.io/en/latest/api/#requests.Session.request)
```
    from qa_testlab.handlers.rest_api_hadler import RestfullApiClient
    
    @pytest.fixture
    def rest():
        return RestfullApiClient(settings.rest_url)
```
```
    Выполнение POST + json content type запроса:
    rest.call_api(method='post', path='/login', request_data={'json': {'login': username, 'password': password}}))
```    
```
    Выполнение POST + form-encoded content type запроса:
    rest.call_api(method='post', path='/', request_data={'data': {'id': 'value'}})
```    
```
    Выполнение GET запроса:
    rest.call_api(method='get', path='/getresult', request_data={'params': {'cid': cid}})
```
```
    Выполнение DELETE запроса:
    rest.api_client.call_api(method='delete', path='/logout', request_data={'cookies': {'auth_token': f'Bearer token'}})
```
```
    Выполнение POST + FILES запроса:
    rest.api_client.call_api(method='delete', path='/logout', request_data={
        'files': {'body': full_path.open(mode='rb')}, 
        'data': {'group': some_group}
    })
```

- **Logger** из модуля qa_testlab.handlers.logs_handler позволяет логировать любые действия в консоль или файл.

### Конфигурирование
Базовая конфигурация сервисов, путей, доступа и браузера содержится в модуле qa_testlab.settings
Переопределять параметры в проектном модуле нужно следующим образом:
    
    browser_name = qa_testlab.settings.browser_name = 'firefox'

### Веб-драйвер
Экземпляр сконфигурированного браузера доступен через глобальную переменную _driver_instance модуля 
qa_testlab.web_driver.driver. Инициализируется веб-драйвер путём вызова метода init_driver(browser_name, 
browser_version=None, is_run_locally=False, headless=True). 

Получить экземпляр веб-драйвера можно вызвав метод get_driver() без параметров, при этом, если веб-драйвер не был ранее
вызван, то он проинициализируется с параметрами указанными в settings.

Поддерживаемые браузеры - chrome, firefox и edge (обязательный параметр browser_name). 

Так же браузер может быть запущен локально (is_run_locally=True) или в selenium grid (is_run_locally=False, а в 
параметре grid_url указан корректный адрес selenium hub). При запуске локально, соответствующий веб-драйвер будет 
автоматически загружен для существующей версии браузера в системе (см. https://pypi.org/project/webdriver-manager/).  

Если указан параметр headless=True, то браузер будет запущен в headless mode, т.е. без отображения самого окна браузера. 
Этот режим доступен только в chrome и firefox.

Метод close_driver() закрывает веб-драйвер.

### Прочее
no_wait декоратор из qa_testlab.web_driver.decorators необходим для того, чтобы отключить ожидание элемента на странице.

Модуль qa_testlab.web_driver.expected_conditions содержит несколько callable классов для ожидания элемента по различным
критериям (тексту, элементы в списке). Пример использования: 
```
    from qa_testlab.webdriver.expected_conditions import element_has_text
    from selenium.webdriver.support.wait import WebDriverWait
    
    WebDriverWait(self.driver, timeout).until(element_has_text(element))
```