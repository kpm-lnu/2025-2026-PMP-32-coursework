.PHONY: all install rosenbrock seird clean

all: install rosenbrock seird

install:
	pip install -r requirements.txt

rosenbrock:
	python Rosenbrock.py

seird:
	python SEIRD-model.py

clean:
	rm -f *.png
