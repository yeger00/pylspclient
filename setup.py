#!/usr/bin/env python
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

with open("README.md", "r") as fh:
    long_description = fh.read()

class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


install_requires=["enum34;python_version<'3.4'"]
tests_require=["pytest", "pytest_mock"] + install_requires

setup(
    name="pylspclient",
    version="0.0.2",
    author="Avi Yeger",
    author_email="yeger00@gmail.com",
    description="LSP client implementation in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yeger00/pylspclient",
    packages=find_packages(),
    install_requires=install_requires,
    tests_require=tests_require,
    cmdclass={"test": PyTest},
)
