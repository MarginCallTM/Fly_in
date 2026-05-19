MAP ?= maps/easy/01_linear_path.txt

.PHONY: install run debug clean lint lint-strict

install:
	pip install -r requirements.txt

run:
	python main.py $(MAP)

debug:
	python -m pdb main.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

lint:
	flake8 . --exclude=.venv,__pycache__ && \
	mypy . --warn-return-any \
	       --warn-unused-ignores \
	       --ignore-missing-imports \
	       --disallow-untyped-defs \
	       --check-untyped-defs \
	       --exclude .venv

lint-strict:
	flake8 . --exclude=.venv,__pycache__ && \
	mypy . --strict --exclude .venv
