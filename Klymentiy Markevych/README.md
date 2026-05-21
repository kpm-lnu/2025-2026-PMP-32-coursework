# Ансамблеві метамоделі машинного навчання в задачах апроксимації багатовимірних функцій та епідеміологічних систем типу SEIRD
 
Маркевич Климентій Володимирович, ПМп-32  
 
## Опис
 
Репозиторій містить програмну реалізацію метамоделей машинного навчання для апроксимації:
- функції Розенброка.
- цільового функціоналу SEIRD-моделі COVID-19.
Реалізовано та порівняно чотири методи: MLP, SVR, Random Forest та Stacking.
 
## Структура репозиторію
 
```
.
├── Rosenbrock.py       # Метамоделі для функції Розенброка
├── SEIRD-model.py      # Метамоделі для SEIRD-системи COVID-19
├── requirements.txt    # Залежності Python
├── Makefile            # Команди для запуску
└── README.md
```
 
## Вимоги
 
- Python 3.10 або новіший
- pip
## Встановлення та запуск
 
### Через Makefile (рекомендовано)
 
```bash
# Встановити залежності та запустити обидва скрипти
make all
 
# Або окремо:
make install       # встановити залежності
make rosenbrock    # запустити Rosenbrock.py
make seird         # запустити SEIRD-model.py
make clean         # видалити згенеровані PNG-файли
```
 
### Вручну
 
```bash
pip install -r requirements.txt
python Rosenbrock.py
python SEIRD-model.py
```
 
## Результати
 
Після запуску у поточній директорії з'являться PNG-файли з графіками:
 
**Rosenbrock.py:**
- `rosenbrock_true_vs_pred_orig_MLP.png`
- `rosenbrock_true_vs_pred_orig_SVR.png`
- `rosenbrock_true_vs_pred_orig_RF.png`
- `rosenbrock_true_vs_pred_orig_Stacking.png`
- `rosenbrock_surface_orig.png`
  
**SEIRD-model.py:**
- `seird_dynamics.png`
- `seird_true_vs_pred_MLP.png`
- `seird_true_vs_pred_SVR.png`
- `seird_true_vs_pred_RF.png`
- `seird_true_vs_pred_Stacking.png`
- `seird_beta_vs_integral.png`
