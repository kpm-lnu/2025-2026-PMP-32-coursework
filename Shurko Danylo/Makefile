# Використання:
#   make help              — показати список доступних команд
#   make install           — встановити Python-залежності у віртуальне середовище
#   make notebooks         — запустити Jupyter Notebook
#   make build-layer       — зібрати Lambda-шар для Terraform
#   make terraform-apply   — розгорнути інфраструктуру в AWS
#   make clean             — видалити build artifacts

# ===== Конфігурація =====

PYTHON      := python3
PIP         := $(PYTHON) -m pip
VENV_DIR    := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP    := $(VENV_DIR)/bin/pip

# Каталоги
LAMBDAS_DIR     := lambdas
INFRA_DIR       := infrastructure
NOTEBOOKS_DIR   := notebooks

# Lambda layer
REQUIREMENTS_LAMBDA := requirements-lambda.txt
REQUIREMENTS_NOTEBOOKS := requirements-notebooks.txt
LAYER_DIR          := layers/scraping_layer/python
LAMBDA_PLATFORM    := manylinux2014_x86_64
LAMBDA_PYTHON_VER  := 3.13

# ===== Основна ціль =====

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Доступні команди:"
	@echo ""
	@echo "  Налаштування середовища:"
	@echo "    make venv              створити віртуальне середовище у .venv/"
	@echo "    make install           встановити Python-залежності"
	@echo "    make install-dev       встановити dev-залежності (jupyter, ruff, pytest)"
	@echo ""
	@echo "  Запуск ноутбуків:"
	@echo "    make notebooks         запустити Jupyter Notebook"
	@echo "    make run-summary       виконати 00_summary_statistics.ipynb"
	@echo ""
	@echo "  Lambda:"
	@echo "    make build-layer       зібрати Lambda-шар (Linux-сумісні бібліотеки)"
	@echo ""
	@echo "  Terraform / AWS:"
	@echo "    make terraform-init    ініціалізувати Terraform"
	@echo "    make terraform-plan    переглянути план змін"
	@echo "    make terraform-apply   розгорнути інфраструктуру"
	@echo "    make terraform-destroy видалити інфраструктуру"
	@echo ""
	@echo "  Якість коду:"
	@echo "    make lint              перевірити стиль коду (ruff)"
	@echo "    make format            автоматично відформатувати код"
	@echo ""
	@echo "  Очищення:"
	@echo "    make clean             видалити Lambda-шар та кеші"
	@echo "    make clean-all         видалити також віртуальне середовище"

# ===== Налаштування середовища =====

.PHONY: venv
venv:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		echo "Створення віртуального середовища у $(VENV_DIR)/..."; \
		$(PYTHON) -m venv $(VENV_DIR); \
		$(VENV_PIP) install --upgrade pip setuptools wheel; \
	else \
		echo "Віртуальне середовище $(VENV_DIR)/ вже існує."; \
	fi

.PHONY: install
install: venv
	@echo "Встановлення Python-залежностей для ноутбуків..."
	$(VENV_PIP) install -r $(REQUIREMENTS_NOTEBOOKS)
	@echo "Готово. Активуйте середовище: source $(VENV_DIR)/bin/activate"

.PHONY: install-dev
install-dev: install
	@echo "Встановлення dev-залежностей..."
	$(VENV_PIP) install jupyter ruff pytest ipykernel
	$(VENV_PYTHON) -m ipykernel install --user --name=tech-skills-insights \
		--display-name="Python (tech-skills-insights)"
	@echo "Готово. Kernel зареєстровано в Jupyter."

# ===== Запуск ноутбуків =====

.PHONY: notebooks
notebooks: install-dev
	@echo "Запуск Jupyter Notebook..."
	$(VENV_PYTHON) -m jupyter notebook $(NOTEBOOKS_DIR)/

.PHONY: run-summary
run-summary: install-dev
	@echo "Виконання 00_summary_statistics.ipynb..."
	$(VENV_PYTHON) -m jupyter nbconvert \
		--to notebook --execute --inplace \
		$(NOTEBOOKS_DIR)/00_summary_statistics.ipynb

# ===== Збирання Lambda-шару =====

.PHONY: build-layer
build-layer:
	@echo "Cleaning old layer files..."
	rm -rf $(LAYER_DIR)
	@echo "Downloading dependencies for Lambda layer..."
	pip install -r $(REQUIREMENTS_LAMBDA) -t $(LAYER_DIR) \
		--platform $(LAMBDA_PLATFORM) \
		--only-binary=:all: \
		--python-version $(LAMBDA_PYTHON_VER)
	@echo "Done! Layer dependencies are ready for Terraform."

# ===== Terraform =====

.PHONY: terraform-init
terraform-init:
	@echo "Ініціалізація Terraform..."
	cd $(INFRA_DIR) && terraform init

.PHONY: terraform-plan
terraform-plan:
	@echo "Перегляд плану Terraform..."
	cd $(INFRA_DIR) && terraform plan

.PHONY: terraform-apply
terraform-apply: build-layer
	@echo "Розгортання інфраструктури в AWS..."
	cd $(INFRA_DIR) && terraform apply

.PHONY: terraform-destroy
terraform-destroy:
	@echo "УВАГА: цю команду буде видалено всі ресурси AWS!"
	@echo "Для продовження натисніть Enter, для відміни — Ctrl+C."
	@read confirm
	cd $(INFRA_DIR) && terraform destroy

# ===== Якість коду =====

.PHONY: lint
lint: install-dev
	@echo "Перевірка стилю коду..."
	$(VENV_PYTHON) -m ruff check $(LAMBDAS_DIR) $(NOTEBOOKS_DIR)

.PHONY: format
format: install-dev
	@echo "Форматування коду..."
	$(VENV_PYTHON) -m ruff format $(LAMBDAS_DIR) $(NOTEBOOKS_DIR)
	$(VENV_PYTHON) -m ruff check --fix $(LAMBDAS_DIR) $(NOTEBOOKS_DIR)

# ===== Очищення =====

.PHONY: clean
clean:
	@echo "Cleaning temporary layer files..."
	rm -rf $(LAYER_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ipynb_checkpoints" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned successfully."

.PHONY: clean-all
clean-all: clean
	@echo "Видалення віртуального середовища..."
	rm -rf $(VENV_DIR)
	@echo "Готово. Для відновлення запустіть: make install"