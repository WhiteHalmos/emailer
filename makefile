.PHONY: test_all init test yapf lint cover upload clean travis

test_all: test lint cover

init:
	pipenv install --python 3.7 --dev

test:
	pipenv run pytest tests

yapf:
	pipenv run yapf -ri .

lint:
	pipenv run yapf -rd .
	pipenv run pytype
	pipenv run pylint emailer tests

cover:
	pipenv run coverage run -m pytest
	pipenv run coverage report

upload: test_all
	tox
	python3.7 setup.py sdist bdist_wheel
	twine upload dist/*
	make clean

clean:
	rm -rf build dist .tox

travis:
	pip install --upgrade pipenv
	pipenv install --dev --skip-lock
