import allure
from selenium.webdriver.common.by import By

from qa_testlab.settings import logger
from qa_testlab.webdriver.page_objects import WebElement, HtmlElement, HtmlElements


class TableHeader(WebElement):
    items = HtmlElements('Поля заголовка таблицы', By.CSS_SELECTOR, 'tr th')

    def __repr__(self):
        return 'Заголовок таблицы'

    @property
    def text(self):
        return self.values

    @property
    def values(self):
        items = self.items
        return [i.text for i in items] if len(items) > 0 else []

    @allure.step("{0} содержит {size} столбцов")
    def has_size(self, size: int):
        assert len(self.items) == size, f'Количество столбцов таблицы не совпадает: {len(self.items)} != {size}'


class TableRow(TableHeader):
    items = HtmlElements('Поле таблицы', By.CSS_SELECTOR, 'td')

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'Строки таблицы: {self.text}'


class Table(WebElement):
    """
    Класс представляющий элемент веб-интерфейса Table (таблица)
    """

    header = HtmlElement('Заголовок таблицы', By.TAG_NAME, 'thead', ui_type=TableHeader)
    rows = HtmlElements('Строки таблицы', By.CSS_SELECTOR, 'tbody tr', ui_type=TableRow)

    @property
    def values(self):
            return [r.values for r in self.rows]

    @property
    def columns(self):
        table = {}
        rows = [r.values for r in self.rows]
        for i, k in enumerate(self.header.values):
            column = [r[i] for r in rows]
            table.update({k: column})
        return table

    @property
    def size(self):
        return len(self.rows)

    def get_column(self, name: str):
        column = [c for c in self.columns if c.name == f'Колонка "{name}"']
        assert len(column) > 0, f'Колонка с названием {name} не найдена.'
        if len(column) > 1:
            logger.warn(f'Колонок с именем "{name}" больше, чем одна.')
        return column[0]

    @allure.step("{0} содержит {size} строк")
    def has_size(self, size: int):
        assert self.size == size, f'Количество строк таблицы не совпадает: {self.size} != {size}'

    @allure.step('Получает строку таблицы по значению {value} колонки {column}')
    def get_row_by_value(self, column: str, value: str) -> TableRow:
        for i, r in enumerate(self.get_column(column)):
            if r.text == value:
                row_num = i
                return self.rows[row_num]

    @allure.step('Проверяет, что строк в {0} больше чем {rows_greater_than}')
    def is_not_empty(self, rows_greater_than: int = 0):
        assert len(self.rows) > rows_greater_than, f'Строк в таблице меньше, чем {rows_greater_than}'

    @allure.step('Сравнивает данные в {0}, игнорируя сортировку={in_any_order}')
    def has_values(self, in_any_order=False, **kwargs):
        """
        Проверяет данные таблицы
        Args:
            in_any_order (bool): True - не учитывает сортировку значений, False - учитывает
            **kwargs: дополнительные параметры список строк или столбцов. Формат:
                    rows=[['col1_row1', 'col2_row1'], ['col1_row2', 'col2_row2']...[]]
                    columns=['col1_title', 'col2_title']
        """
        assert all([k == 'rows' or k == 'columns' for k in kwargs.keys()]), \
            'Допустимые параметры rows и/или columns, формат значений - вложенный список'
        columns = kwargs.get('columns') if 'columns' in kwargs.keys() else None
        rows = kwargs.get('rows') if 'rows' in kwargs.keys() else None
        if columns:
            table_columns = sorted(self.header.values) if in_any_order else self.header.values
            expected_columns = sorted(columns) if in_any_order else columns
            assert table_columns == expected_columns, \
                f'Колонки "{table_columns}" в "{self.name}" не соответствуют ожидаемым: {columns}'
        if rows:
            table_values = sorted(self.values) if in_any_order else self.values
            expected_values = sorted(rows) if in_any_order else rows
            assert table_values == expected_values, \
                f'Значения "{table_values}" в "{self.name}" не соответствуют ожидаемым: {expected_values}'