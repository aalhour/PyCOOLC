# PyCOOLC Makefile
# A COOL to MIPS compiler written in Python

.PHONY: help venv install clean unit-tests integration-test test lint examples

# Default target
.DEFAULT_GOAL := help

# Python and virtual environment
PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
PYCOOLC := $(VENV_BIN)/pycoolc

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RESET := \033[0m

##@ General

help: ## Display this help message
	@echo "$(CYAN)PyCOOLC$(RESET) - COOL to MIPS Compiler"
	@echo ""
	@echo "$(YELLOW)Usage:$(RESET)"
	@echo "  make $(GREEN)<target>$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2 } \
		/^##@/ { printf "\n$(YELLOW)%s$(RESET)\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Development

venv: ## Create virtual environment
	@echo "$(CYAN)Creating virtual environment...$(RESET)"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)Done!$(RESET) Activate with: source $(VENV)/bin/activate"

install: ## Install package in development mode
	@echo "$(CYAN)Installing package...$(RESET)"
	$(PIP) install -e ".[dev]"

##@ Testing

unit-tests: ## Run unit tests
	@echo "$(CYAN)Running unit tests...$(RESET)"
	$(PYTEST) tests/ -v --tb=short

integration-test: ## Run integration tests with SPIM
	@echo "$(CYAN)Running integration tests...$(RESET)"
	@./bin/integration-test

test: unit-tests integration-test ## Run all tests (unit + integration)

lint: ## Check for linter errors
	@echo "$(CYAN)Checking for linter errors...$(RESET)"
	$(PYTHON) -m py_compile pycoolc/*.py pycoolc/**/*.py

##@ Examples

examples: ## Compile all example programs
	@echo "$(CYAN)Compiling example programs...$(RESET)"
	@for f in examples/*.cl; do \
		echo "  Compiling $$f..."; \
		$(PYCOOLC) "$$f" -o "$${f%.cl}.s" 2>&1 || echo "    $(YELLOW)Warning: $$f failed$(RESET)"; \
	done
	@echo "$(GREEN)Done!$(RESET)"

run-hello: ## Compile and run hello_world.cl
	@echo "$(CYAN)Compiling hello_world.cl...$(RESET)"
	$(PYCOOLC) examples/hello_world.cl -o examples/hello_world.s
	@echo "$(CYAN)Running with SPIM...$(RESET)"
	@if command -v spim >/dev/null 2>&1; then \
		spim -file examples/hello_world.s; \
	elif [ -f /Applications/QtSpim.app/Contents/MacOS/QtSpim ]; then \
		echo "Use QtSpim GUI to run examples/hello_world.s"; \
	else \
		echo "$(YELLOW)SPIM not found. Install from https://sourceforge.net/projects/spimsimulator/$(RESET)"; \
	fi

##@ Cleanup

clean: ## Clean build artifacts and caches
	@echo "$(CYAN)Cleaning...$(RESET)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ __pycache__/
	rm -rf pycoolc/__pycache__/ pycoolc/**/__pycache__/
	rm -rf tests/__pycache__/ tests/**/__pycache__/
	rm -f parser.out parsetab.py
	rm -f examples/*.s
	@echo "$(GREEN)Done!$(RESET)"

clean-all: clean ## Clean everything including venv
	rm -rf $(VENV)

