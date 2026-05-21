# RBF Surrogate Modeling

Курсова робота: застосування радіально-базисних функцій (RBF)
для сурогатного моделювання алгебраїчних функцій та
епідеміологічних систем типу SEIRD.

## Вимоги

Python 3.10+

Встановити залежності:

```bash
pip install numpy scipy matplotlib
```

## Запуск

### Розділ 1 — Функція Розенброка

```bash
cd rosenbrock
python rbf_rosenbrock.py
```

Що відбувається:
- будується RBF-сурогат для функції Розенброка на сітці 6×6
- виводяться метрики якості (RMSE, R², MAE, MAX_RE)
- зберігаються графіки у поточну папку:
  - `rbf_3d_comparison.png` — 3D поверхні справжньої та сурогатної функції
  - `rbf_convergence.png` — збіжність моделі
  - `rbf_scatter_gaussian.png` — scatter для Gaussian RBF
  - `rbf_scatter_multiquadric.png` — scatter для Multiquadric RBF
  - `rbf_scatter_tps.png` — scatter для Thin Plate Spline RBF

### Розділ 2 — SEIRD модель COVID-19

```bash
cd seird
python rbf_seird.py
```

⚠️ Час виконання: ~2–5 хвилин (розв'язання системи ОДУ
для кожної точки навчальної та тестової вибірок).

Що відбувається:
- моделюються три сценарії епідемії (довічний імунітет,
  повторне зараження, локдаун)
- будується RBF-сурогат для функціонала ψ(β, γ) на сітці 6×6
- проводиться оптимізація параметра β
- зберігаються графіки у поточну папку:
  - `seird_g1_1_dynamika.png` — сценарій 1
  - `seird_g1_2_dynamika.png` — сценарій 2
  - `seird_g1_3_dynamika.png` — сценарій 3 (локдаун)
  - `seird_g2_1_surrogat.png` — scatter Gaussian
  - `seird_g2_2_surrogat.png` — scatter Multiquadric
  - `seird_g2_3_surrogat.png` — scatter Thin Plate Spline
  - `seird_g3_zbizhist.png` — збіжність
  - `seird_g4_1_typy_true.png` — 3D справжня поверхня ψ
  - `seird_g4_2_typy_surrogate.png` — 3D сурогатна поверхня ψ
  - `seird_g5_1_optym_dynamics.png` — динаміка I(t)
  - `seird_g5_2_optym_bars.png` — порівняння цільової функції

## Автор

Мурмило Олександр Васильович  
Групи ПМп-32, ЛНУ імені Івана Франка, 2026
