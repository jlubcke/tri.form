.PHONY: clean-pyc clean-build docs clean

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "tag - set a tag with the current version number"
	@echo "release - check release tag and build release artifacts"

clean: clean-build clean-pyc
	rm -fr htmlcov/

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-docs:
	rm -f docs/tri*.rst

lint:
	flake8 lib/tri tests

test:
	tox

coverage:
	tox -e coverage

docs:
	tox -e docs

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	python setup.py bdist_egg
	ls -l dist

tag:
	python setup.py tag

release: clean
	python setup.py release_check
	python setup.py sdist
	python setup.py bdist_wheel
	python setup.py bdist_egg
	ls -l dist
