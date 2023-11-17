# Makefile for videobookmarks


# Virtual environment setup. These can be specified with different paths if needed.
# virtual env is just added for ease of use, and is not required to
# run videobookmarks

VENV_NAME := venv
VENV_BIN := $(VENV_NAME)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
FLASK := $(VENV_BIN)/flask

# Start virtual environment
venv:
	source $(VENV_BIN)/activate

# Install dependencies
install:
	$(PIP) install -r requirements.txt

# @TODO: we need a clear way to run the application
# run:
    # run command defined here

# Run unit tests
# these can be grouped in the future for easier maintainability
test:
	pytest

# Clean up compiled Python files and __pycache__
clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

# Manual
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	# @echo "  run        - Run the Flask application"
	@echo "  test       - Run unit tests"
	@echo "  clean      - Clean up compiled Python files and __pycache__"
	@echo "  help       - Display this help message"