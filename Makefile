help:
		@echo 'Makefile for Tinker                              '
		@echo 'Usage:                                           '
		@echo '   make install          install                                          '
		@echo '   make test             run test cases          '
		@echo '   make mybot            start bot               '
		@echo '   make develop          develop                 '
		@echo '   make docs             update docs             '
		@echo '   make upload           upload to pypi          '
		@echo '   make clean            clean                   '

install:
	pip install -r requirements.txt

test:
	cd wechatbot; pytest
	make clean

clean:
	find . \( -name "*.pyc" -o -name "*.log" -o -name "*.swp" -o -name "*.swo" \) -delete

mybot:
	python -m wechatbot.bot

develop:
	python -m wechatbot.ping

docs:
	cd wechatbot
	cd docs; make html
	open docs/_build/html/index.html

upload:
	rm -rf dist/*
	python setup.py sdist bdist_wheel
	twine upload dist/*

.PHONY: docs
