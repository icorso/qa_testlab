import http.cookies
from urllib.parse import urlunparse, urlsplit

import requests
from requests import Response

from qa_testlab.settings import logger


class RestfullApiClient(object):
    def __init__(self, url, username=None, password=None):
        self.url = url
        self.session = requests.Session()
        self.username = username if username else 'admin'
        self.password = password if password else 'admin'

    def call_api(self, method: str, path: str, request_data: dict = None, log_details: bool = False) -> Response:
        """Вызов API запроса
        Args:
            method (str): http метод GET, POST и т.д.
            path (str): путь к ресурсу, например /user/123
            request_data: любой из доступных необязательных параметров request:
            params, data, headers, cookies, files, auth, timeout, allow_redirects=True, proxies, hooks, stream,
            verify, cert, json. Например:
             - для GET запроса, {'params': {'id': group_id}};
             - для POST + FILES:
                {
                    'files': {'body': full_path.open(mode='rb')},
                    'data': {'group': some_group}
                }
             - для POST content type JSON: {'json': {'id': some_id}}
            log_details (bool): логировать header и cookies

        Returns: экземпляр класса Response
        """
        u = urlsplit(self.url)
        data = request_data if request_data else {}
        response = self.session.request(method, urlunparse((u.scheme, u.netloc, path, '', '', '')), **data)
        request_log = f'Request params:\n' \
                      f'- method: {method}\n- url: {self.url}{path}\n- data: {data}'

        response_log = f'Response params:\n' \
                       f'- status code: {response.status_code}\n- response text: {response.text}' \

        if log_details:
            request_log = f'{request_log}\n' \
                          f'- headers: {self.session.headers}\n' \
                          f'- cookies: {self.session.cookies.get_dict()}'
            response_log = f'{response_log}\n' \
                           f'- headers: {response.headers}\n' \
                           f'- cookies: {response.cookies.get_dict()}'

        log_entry = f'{request_log}\n{response_log}'

        if response.status_code == 500:
            logger.fatal(f'Status code {response.status_code} received.\n{log_entry}')
        elif not 200 <= response.status_code <= 299:
            logger.error(f'Status code {response.status_code} received.\n{log_entry}')
        else:
            logger.info(log_entry)
        return response

    def with_headers(self, headers: dict):
        self.session.headers.update(headers)
        return self

    def with_cookie(self, cookie: str):
        simple_cookie = http.cookies.SimpleCookie(cookie)
        self.session.cookies.update(simple_cookie)
        return self

    def login(self, method: str, path: str, **credentials) -> Response:
        return self.call_api(method, path, {'json': {**credentials}})
