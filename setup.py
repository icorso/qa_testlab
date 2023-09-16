from setuptools import setup, find_packages

NAME = "qa_testlab"
VERSION = "0.1.7"


def readme():
    with open('README.md') as f:
        return f.read()


setup(name=NAME,
      version=VERSION,
      description='QA team tools for automation testing',
      long_description=readme(),
      classifiers=[
          'Development Status :: 4 - Beta',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Environment :: Plugins',
          'Topic :: Software Development :: Testing',
      ],
      author='Maxim Filippov',
      author_email='mfilippov@isgneuro.com',
      url='https://github.com/ISGNeuroTeam/qa_testlab',
      install_requires=[
          'selenium>=4.11.0',
          'allure-pytest>=2.13.2',
          'webdriver-manager>=4.0.0',
          'fsspec>=2023.6.0',
          'pixelmatch>=0.3.0',
          'Pillow~=9.3.0',
          'paramiko>=3.3.1',
          'requests>=2.31.0'
      ],
      packages=find_packages(),
      setup_requires=['wheel'],
      zip_safe=False)
