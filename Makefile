#.SILENT:

BASE_PTH = $(shell pwd)

all:
	echo -e "Required section:\n\
 venv - create an virtual environment\n\
 clean - clean build artifacts\n\
 build - build an application\n\
"

venv:
	echo Create venv
	python3 -m venv ./venv
	. ./venv/bin/activate
	./venv/bin/python3 -m pip install --upgrade pip setuptools wheel build

clean:
	echo "Cleaning build artifacts..."
	rm -rf ./build
	rm -rf ./dist
	rm -rf ./qa_testlab.egg-info

build: venv clean
	echo "Building application..."
	. ./venv/bin/activate
	export PYTHONPATH=.; ./venv/bin/python3 -m build --wheel