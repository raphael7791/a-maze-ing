.PHONY: install run debug clean lint lint-strict build

install:
	pip install flake8 mypy build

run:
	python3 a_maze_ing.py config.txt

debug:
	python3 -m pdb a_maze_ing.py config.txt

clean:
	rm -rf __pycache__ mazegen/__pycache__ .mypy_cache
	rm -rf build dist *.egg-info

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

build:
	python3 -m build
	cp dist/mazegen-*.whl . 2>/dev/null || true
	cp dist/mazegen-*.tar.gz . 2>/dev/null || true
