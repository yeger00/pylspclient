# pylspclient
[![image](https://img.shields.io/pypi/v/pylspclient.svg)](https://pypi.org/project/pylspclient/)
[![Test Package](https://github.com/yeger00/pylspclient/actions/workflows/test-pkg.yml/badge.svg)](https://github.com/yeger00/pylspclient/actions/workflows/test-pkg.yml)
[![image](https://img.shields.io/github/license/python-ls/python-ls.svg)](https://github.com/yeger00/pylspclient/blob/main/LICENSE)

A Python 3.10+ implemntation of a [LSP](https://microsoft.github.io/language-server-protocol/) client.


# What is LSP?


# Getting started
## Installation
```
pip install pylspclient
```

# Contributing
In order to contribute you need to make sure your PR passes all the [Test Package](https://github.com/yeger00/pylspclient/blob/main/.github/workflows/test-pkg.yml) steps. You can run it locally as well:

## Run the tests
```
pip install -e .
pip install -r requirements.test.txt
pytest test
```

## Run the linter
```
ruff check .
```

# License
This project is made available under the MIT License.
