SHELL := /bin/bash


.PHONY: \
install-packages \
list-dev-packages \
list-packages \
noop \
python-version \
shell \
small-tests \
update-packages \
z_end


.DEFAULT_GOAL := small-tests

noop:
	echo "NO OP"

python-version:
	python --version
	python3 --version

shell:
	pipenv shell

update-packages: python-version
	pipenv update --dev

install-packages: python-version
	pipenv install --dev

list-packages: python-version
	pipenv lock -r

list-dev-packages: python-version
	pipenv lock -r --dev

small-tests:
	pipenv run pytest --durations 0 -r A --verbose
