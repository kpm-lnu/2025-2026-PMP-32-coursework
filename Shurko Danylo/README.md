Аналітичний комплекс для дослідження українського IT-ринку праці на основі даних з відкритих джерел.

## Зміст

- [Що це таке](#що-це-таке)
- [Структура репозиторію](#структура-репозиторію)
- [Швидкий старт](#швидкий-старт)
- [Запуск ноутбуків](#запуск-ноутбуків)
- [Розгортання інфраструктури](#розгортання-інфраструктури)
- [Доступ до даних](#доступ-до-даних)
- [Команди Makefile](#команди-makefile)
- [Технології](#технології)

## Що це таке

Система для:

1. **Безперервного збору** оголошень про вакансії з jobs.dou.ua та djinni.co
2. **Дедуплікації** через семантичні embedding-вектори
3. **Витягу технологічних навичок** з описів вакансій за допомогою LLM
4. **Регресійного моделювання** залежності заробітної плати від набору навичок
5. **Аналізу спільної появи** навичок для виявлення технологічних кластерів

## Структура репозиторію

```
├── infrastructure/           # Terraform-конфігурація для AWS
├── lambdas/                  # AWS Lambda функції (DOU + Djinni)
│   ├── dou/
│   │   ├── dou_dispatcher.py
│   │   ├── dou_producer.py
│   │   ├── dou_worker.py
│   │   └── dou_aggregator.py
│   │   
│   └── djinni/
│       └── djinni_parser.py
│
├── notebooks/                # обчислювальні ноутбуки (Jupyter)
│   ├── 00_summary_statistics.ipynb
│   ├── 01_data_cleaning_and_deduplication.ipynb
│   ├── 02_skill_extraction.ipynb
│   ├── 03_merge.ipynb
│   ├── 04_regression.ipynb
│   └── 05_skill_gap.ipynb
├── Makefile                  # автоматизація типових команд
├── requirements-lambda.txt
├── requirements-notebooks.txt      
├── .gitignore
└── README.md                 # цей файл
```

## Швидкий старт

### Вимоги

- Python 3.10+
- GNU Make
- Terraform 1.5+ (для розгортання інфраструктури)
- Обліковий запис AWS (для розгортання Lambda-функцій)
- Kaggle або Google Colab з NVIDIA T4 GPU (для блокнота екстракції скілів)

### Перший запуск

```bash
git clone https://github.com/danetell0/2025-2026-PMP-32-coursework.git
cd coursework
make install            # створить .venv/ і встановить залежності
```

Після цього всі основні команди доступні через `make`. Перелік — `make help`.

## Запуск ноутбуків

### На Kaggle (рекомендовано)

Дані вже опубліковано як Kaggle Dataset. Найшвидший шлях відтворити аналіз:

1. Створіть Kaggle Notebook
2. **Add Input** → знайти потрібний датасет (див. [розділ нижче](#доступ-до-даних))
3. Завантажте потрібний `.ipynb` з папки `notebooks/`
4. Натисніть **Run All**

### Локально

```bash
make notebooks          # запустить Jupyter у браузері
```

Або через прямий виклик однієї команди:

```bash
make run-summary        # виконає 00_summary_statistics.ipynb
```

### Порядок виконання

Ноутбуки нумеровані за послідовністю — кожен наступний залежить від виходу попереднього:

| Ноутбук | Призначення | Вхідні дані | Вихідні дані |
|---|---|---|---|
| `01_data_cleaning_and_deduplication.ipynb` | Очищення та нормалізація сирих даних, двоетапна дедуплікація | step1 (DOU + Djinni Parquet) | step2 Parquet |
| `02_skill_extraction.ipynb` | Витяг навичок через Qwen2.5-3B | step2 описи вакансій | `skills_checkpoint.json` |
| `03_merge.ipynb` | Об'єднання даних із витягнутими скілами та нормалізація | step2 + checkpoint | step3 Parquet |
| `04_regression.ipynb` | Множинна лінійна регресія | step3 | `regression_results.csv`, `regression_summary.txt`, `regression_top_skills.png` |
| `05_skill_gap.ipynb` | Аналіз асоціативних правил | step3 | `skillgap_top_pairs.csv`, `skillgap_recommendations.csv`, `skillgap_heatmap.png` |
| `00_summary_statistics.ipynb` | Зведена статистика результатів | step2, step3, CSV-результати | вивід у клітинках |

Якщо потрібно лише відтворити фінальний аналіз (без повторного збору даних та LLM-екстракції), використовуйте опубліковані Kaggle-датасети та запускайте лише `04`, `05` і `00`.

### Особливості ноутбука `02_skill_extraction`

Вимагає **GPU NVIDIA T4** (доступний безкоштовно в Kaggle) або кращий. Тривалість — близько 6–10 годин на 27 720 вакансіях. Зберігає checkpoint після кожного батча, тож можна відновити при перериванні.

## Розгортання інфраструктури

Уся хмарна архітектура описана у Terraform-файлах у каталозі `infrastructure/`. Розгортається:

| Ресурс | Кількість | Призначення |
|---|---|---|
| AWS Lambda функції | 5 | Парсинг DOU (4) + Djinni (1) |
| Amazon SQS черги | 2 | Основна + Dead Letter Queue |
| DynamoDB таблиця | 1 | Зберігання стану (остання оброблена дата) |
| S3 bucket | 1 | Сирі та оброблені дані |
| EventBridge правило | 1 | Щоденний запуск о 04:00 за київським часом |
| IAM ролі та політики | кілька | Дозволи для різних об'єктів |

### Кроки розгортання

1. **Налаштувати AWS credentials:**

   ```bash
   aws configure
   # Введіть Access Key ID, Secret Access Key, регіон (рекомендовано eu-central-1)
   ```

2. **Зібрати Lambda-шар:**

   ```bash
   make build-layer
   ```

   Результат — Linux-сумісні бібліотеки в `layers/scraping_layer/python/`, які Terraform упаковує в Lambda Layer.

3. **Ініціалізувати та розгорнути Terraform:**

   ```bash
   make terraform-init
   make terraform-plan       # переглянути зміни
   make terraform-apply      # розгорнути
   ```

### Перевірка роботи

Після розгортання запустіть Dispatcher вручну для перевірки:

```bash
aws lambda invoke \
  --function-name dou-dispatcher \
  --payload '{}' \
  /tmp/response.json

cat /tmp/response.json
```

Має повернути `{"statusCode": 200, "body": "..."}`.

### Видалення інфраструктури

```bash
make terraform-destroy
```

S3-бакет (якщо в ньому є дані) видаліть окремо:

```bash
aws s3 rm s3://your-bucket-name --recursive
aws s3 rb s3://your-bucket-name
```

### Орієнтовна вартість

При типовому навантаженні (близько 400-500 викликів Lambda на день) — менше **1 USD на місяць** у межах безкоштовного рівня AWS.

## Доступ до даних

Parquet-файли датасету (близько 268 МБ). Доступ:

- **Google Drive** (повний датасет step1 + step2 + step3): <https://drive.google.com/drive/u/0/folders/17-_1x1Yx4iQQ4tGj66Z7_HrpPpqfXRSX>
- **Kaggle Datasets** (для запуску ноутбуків):
  - `tech-skills-step2` — корпус після дедуплікації
  - `tech-skills-step3` — фінальний корпус зі скілами
  - `tech-skills-results` — CSV-результати регресії та skill-gap

Деталі формату даних — в README у Google Drive та у підрозділі 2.5.1 звіту.

## Команди Makefile

Повний список — `make help`. Найчастіше використовувані:

**Налаштування середовища:**

```bash
make venv               # створити .venv/
make install            # встановити основні залежності
make install-dev        # + jupyter, ruff, pytest
```

**Запуск:**

```bash
make notebooks          # запустити Jupyter Notebook
make run-summary        # виконати 00_summary_statistics.ipynb
```

**Lambda:**

```bash
make build-layer        # зібрати Lambda-шар (Linux-сумісні бібліотеки)
```

**Terraform / AWS:**

```bash
make terraform-init     # ініціалізувати Terraform
make terraform-plan     # переглянути план змін
make terraform-apply    # розгорнути інфраструктуру
make terraform-destroy  # видалити інфраструктуру
```

**Якість коду:**

```bash
make lint               # перевірити стиль (ruff)
make format             # автоматично відформатувати
```

**Очищення:**

```bash
make clean              # видалити build artifacts та кеші
make clean-all          # + видалити .venv/
```

## Технології

**Інфраструктура**

- AWS Lambda — serverless обчислення
- Amazon SQS — черги повідомлень
- Amazon S3 — зберігання даних
- DynamoDB — стан пайплайнів
- Amazon EventBridge — планувальник
- Terraform — управління інфраструктурою як кодом

**Обробка даних**

- Python 3.10
- pandas, pyarrow — табличні операції
- BeautifulSoup — парсинг HTML
- sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`) — embedding-вектори
- Qwen2.5-3B-Instruct — витяг навичок з вільнотекстових описів

**Статистичний аналіз**

- statsmodels — множинна лінійна регресія методом OLS
- matplotlib — візуалізація результатів
