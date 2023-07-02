.PHONY: lint type test test-html isort isort-check build upload

PYMODULE:=sbot
TESTS:=tests

all: lint isort-check type build

lint:
	flake8 $(PYMODULE)

type:
	mypy $(PYMODULE)

test:
	pytest --cov=$(PYMODULE) --cov-report=term --cov-report=xml $(TESTS)

test-html:
	pytest --cov=$(PYMODULE) --cov-report=html $(TESTS)

isort-check:
	python -m isort --check $(PYMODULE)

isort:
	python -m isort $(PYMODULE)

build:
	python -m build

upload:
	twine upload dist/*

clean:
	rm -rf dist/* build/*
