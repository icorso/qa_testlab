import os
import subprocess
import tarfile
from pathlib import Path
from time import sleep

import allure
from fsspec.implementations.local import LocalFileSystem
from fsspec.implementations.sftp import SFTPFileSystem

from qa_testlab import settings

logger = settings.logger


def get_fsspec(host=None, port=None, login=None, password=None):
    host = host if host else settings.host
    port = port if port else settings.ssh_port
    login = login if login else settings.ssh_login
    password = password if password else settings.ssh_password

    if settings.host in ('localhost', '0.0.0.0', '127.0.0.1') and int(port) == 22:
        return LocalFileSystemWrapper()
    else:
        return SFTPFileSystemWrapper(
            host=host,
            port=port,
            username=login,
            password=password,
            look_for_keys=False,
            allow_agent=False
        )


class SFTPFileSystemWrapper(SFTPFileSystem):
    def __init__(self, host, **ssh_kwargs):
        super().__init__(host, **ssh_kwargs)

    def run(self, command, status=True, background=False, output=False):
        if background:
            command += ' > /dev/null 2>&1 &'
        stdin, stdout, stderr = self.client.exec_command(command)
        if not status and not output:
            sleep(0.5)
            return
        while not stdout.channel.exit_status_ready():
            pass
        if not output:
            return stdout.channel.exit_status
        else:
            return stdout.readline()


class LocalFileSystemWrapper(LocalFileSystem):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self, command, status=True, background=False, output=False):
        if background:
            command += ' > /dev/null 2>&1 &'
        s = subprocess.s = subprocess.getstatusoutput(command)
        if not output:
            return s[0] if status else None
        else:
            return s[1]


class FSHandler:
    def __init__(self, fsspec):
        self.fsspec = fsspec

    @allure.step('Получает данные из файла {filepath}')
    def get_data_from_file(self, filepath):
        return self.fsspec.cat_file(filepath).decode('utf-8').splitlines(True)

    def directory_content(self, path):
        return [str(f).rsplit('/', 1)[1] for f in self.fsspec.ls(path)]

    def clean_out_directory(self, path, dirs_to_keep=None):
        dirs_to_keep = [] if not dirs_to_keep else dirs_to_keep
        for f in self.fsspec.glob(f'{path}/*'):
            name = f.rsplit("/", 1)[1]
            if self.fsspec.isfile(f):
                self.fsspec.rm_file(f)
            # удаляет не пустой каталог и не в dirs_to_keep списке
            if self.fsspec.isdir(f) and name not in dirs_to_keep and len(self.fsspec.ls(f)) == 0:
                self.fsspec.rmdir(f)

    def copy_file_to_test_project(self, file_path, dir_to_copy_in):
        """
        Копирование файла в локальный каталог. Если каталога на локальной файловой системе
        не существует, он будет создан рекурсивно (создаются все родительские директории)
        Args:
            file_path: str полный путь к файлу на удалённой файловой системе, /opt/otp/file.txt
            dir_to_copy_in: str локальная директория (должна содержать завершающий /), /tmp/subtmp/

        Returns: str Полный путь к скопированному файлу
        """
        filename = file_path.rsplit('/', 1)[1]
        Path(dir_to_copy_in).mkdir(parents=True, exist_ok=True)
        local_file_path = f'{dir_to_copy_in}{filename}'
        self.fsspec.get(file_path, local_file_path)
        logger.info(f'Файл {file_path} скопирован в {dir_to_copy_in}')
        return local_file_path

    @allure.step('Распаковывает архивный файл {src} в папку {dst}')
    def extract_data_from_compressed_file(self, src: str, dst: str = settings.temp_dir):
        """
        Загружает архивный файл в dst каталог и получает его содержимое. Файл может располагаться как на удалённой,
        так и на локальной файловой системе.
        Args:
            :param src: str полный путь к архивному файлу на локальной или удалённой файловой системе,
            например /tmp/file.tar.gz
            :param dst: str путь к папке для распаковки
        """
        file_name = os.path.basename(src)
        local_path = str(Path(dst, file_name))
        self.fsspec.get(src, local_path)  # копирует с удалённой на локальную файловую систему
        data_list = []
        with tarfile.open(local_path) as tar:
            inner_objects = tar.getnames()
            for obj in inner_objects:
                obj_data = tar.extractfile(obj)
                read_data = obj_data.read()
                data_list.append(f'файл "{obj}": {read_data.decode()}')
        return data_list

    @allure.step('Копирование файла {local_path} в {remote_path}')
    def put(self, local_path, remote_path):
        """
        Копирование файла на удалённую файловую систему.
        Args:
            local_path: str полный путь к локальному файлу, который нужно скопировать, /opt/file_a.txt
            remote_path: str полный путь к файлу на удалённой файловой системе, /tmp/file_b.txt
        """
        self.fsspec.put(str(local_path), str(remote_path))
        logger.info(f'Файл "{local_path}" скопирован в "{remote_path}"')

    def copy_local_dir_to_remote(self, local_path, remote_path):
        """
        Копирование каталога с локальной файловой системы на удалённую (в зависимости от конфигурации и на локальную).
        Если в файле конфигурации [fs] host указан локальный адрес и port 22, то копирование происходит в пределах
        локальной файловой системы. Если целевого каталога не существует, то он будет создан вместе со всеми
        промежуточными каталогами.
        Args:
            local_path: str путь к локальному каталогу
            remote_path: str путь к удалённому каталогу
        """
        self.fsspec.makedirs(remote_path, exist_ok=True)
        for item in os.listdir(local_path):
            local_item = os.path.join(local_path, item)
            remote_item = os.path.join(remote_path, item)
            if os.path.isfile(local_item):
                self.fsspec.put(local_item, remote_item)
                logger.info(f'-- {remote_item} скопирован')
            else:
                self.fsspec.mkdirs(remote_item, exist_ok=True)
                logger.info(f'++ {remote_item} каталог создан')
                self.copy_local_dir_to_remote(local_item, remote_item)

    def copy_remote_dir_to_local(self, remote_path, local_path):
        """
        Копирование каталога с удалённой системы на локальную.
        Если в файле конфигурации [fs] host указан локальный адрес и port 22, то копирование происходит в пределах
        локальной файловой системы. Если целевого каталога не существует, то он будет создан вместе со всеми
        промежуточными каталогами.
        Args:
            remote_path: str путь к удалённому каталогу
            local_path: str путь к локальному каталогу
        """
        os.makedirs(local_path, exist_ok=True)
        for item in self.fsspec.glob('{}/*'.format(remote_path)):
            item_name = os.path.basename(item)
            local_item = os.path.join(local_path, item_name)
            if self.fsspec.isfile(item):
                self.fsspec.get_file(item, os.path.join(local_path, item_name))
                logger.info(f'-- {local_item} скопирован')
            else:
                Path(local_item).mkdir(parents=True, exist_ok=True)
                logger.info(f'++ {local_item} каталог создан')
                self.copy_remote_dir_to_local(item, local_item)

    def remove_dir(self, dirpath):
        logger.info(f'удаляется каталог {dirpath} ...')
        if self.fsspec.isdir(dirpath):
            files = self.fsspec.listdir(path=dirpath, detail=False)
            for f in files:
                filepath = os.path.join(dirpath, f)
                if not self.fsspec.isdir(filepath):
                    self.fsspec.rm_file(filepath)
                    logger.info(f'\t-- файл {filepath} удалён')
                else:
                    self.remove_dir(filepath)
            self.fsspec.rmdir(dirpath)
            logger.info(f'каталог {dirpath} удалён')

    def remove_files(self, path, exclusion_mask=None):
        """
        Удаляет все файлы в каталоге (кроме подкаталогов), если не задано исключение по маске.
        Args:
            path: путь к каталогу
            exclusion_mask: маска, например 'json'
        """
        logger.info(f'удаляются файлы из каталога {path}')
        files = (f for f in self.fsspec.glob(f'{path}/*') if self.fsspec.isfile(f))
        for f in files:
            if exclusion_mask and f.endswith(exclusion_mask):
                continue
            self.fsspec.rm_file(f)
            logger.info(f'\t-- {f} удалён')

    def remove_file(self, path_to_file):
        """
        Удаляет файл на удалённой файловой системе.
        Args:
            path_to_file: полный путь к файлу
        """
        logger.info(f'удаляется файл {path_to_file}')
        if self.fsspec.isfile(path_to_file):
            self.fsspec.rm_file(path_to_file)
            logger.info(f'\t-- {path_to_file} удалён')

    @allure.step('Проверяет наличие файла {path_to_file} на файловой системе')
    def should_file_exist(self, path_to_file):
        """
        Проверяет, существует ли файл на удалённой файловой системе.
        Args:
            path_to_file: полный путь к файлу
        """
        assert self.fsspec.isfile(path_to_file), f'Файл {path_to_file} не существует'

    @allure.step('Выполняется команда {command}')
    def run(self, command, status=True, background=False, output=False):
        settings.logger.info(f'\tвыполняется команда: "{command}, с параметрами:'
                             f' status={status}, background={background}, output={output}"')
        return self.fsspec.run(command, status=status, background=background, output=output)


    @allure.step('Ожидает появления файлов в каталогах {dirs} в течение {timeout} сек.')
    def waiting_for_directories_to_fill(self, dirs: list, files_amount=None, timeout=30):
        _timeout = timeout
        for d in dirs:
            is_filled = False
            while not is_filled and timeout > 0:
                if not self.fsspec.isdir(d):  # если каталога нет
                    timeout -= 1
                    sleep(1)
                    continue
                if not files_amount and self.fsspec.listdir(d, detail=False):
                    # если не задано количество файлов и не пустой каталог
                    is_filled = True
                elif files_amount and len(self.fsspec.listdir(d, detail=False)) >= files_amount:
                    # если файлов в каталоге больше или равно заданному количеству файлов
                    is_filled = True
                else:
                    timeout -= 1
                    sleep(1)
            assert is_filled, f'Файлы не появились в каталоге "{d}" в течение "{_timeout}" сек.'
