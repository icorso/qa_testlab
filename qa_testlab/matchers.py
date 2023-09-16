import allure

from qa_testlab.settings import logger


@allure.step('Сравнивает схему с ожидаемой')
def match_dictionaries(original_dict, tested_dict):
    def get_type(value):
        if isinstance(value, dict):
            return {key: get_type(value[key]) for key in value}
        elif isinstance(value, list):
            return [get_type(list_element) for list_element in value]
        else:
            return type(value)
    original_dict_scheme = get_type(original_dict)
    tested_dict_scheme = get_type(tested_dict)
    logger.info(f'Проверочная схема:\n{original_dict_scheme}\nПроверяемая схема:\n{tested_dict_scheme}\n')
    return original_dict_scheme == tested_dict_scheme
