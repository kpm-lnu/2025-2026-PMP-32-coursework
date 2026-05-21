import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
import matplotlib.pyplot as plt
from sklearn.ensemble import StackingRegressor, RandomForestRegressor

def rosenbrock(x1, x2):
    return (1 - x1)**2 + 100 * (x2 - x1**2)**2

np.random.seed(42)

# x1, x2 є [-2, 2]
n_samples = 800
X = np.random.uniform(-2, 2, size=(n_samples, 2))
y_raw = rosenbrock(X[:, 0], X[:, 1])

# Масштабуємо використовуючи ln(1+f), щоб область була [0, 8].
y = np.log1p(y_raw)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

level_a_estimators = [
    ('mlp', make_pipeline(
        StandardScaler(),
        MLPRegressor(
            hidden_layer_sizes=(100, 100),
            activation='tanh',
            solver='lbfgs',
            max_iter=2000,
            random_state=42,
            alpha=1e-4
        )
    )),
    ('svr', make_pipeline(
        StandardScaler(),
        SVR(kernel='rbf', C=100, epsilon=0.01, gamma='scale')
    )),
    ('rf', make_pipeline(
        StandardScaler(),
        RandomForestRegressor(n_estimators=200, random_state=42)
    ))
]

stacking_model = StackingRegressor(
    estimators=level_a_estimators,
    final_estimator=LinearRegression(),
    cv=5
)

stacking_model.fit(X_train, y_train)

models = {
    "MLP":      stacking_model.named_estimators_['mlp'],
    "SVR":      stacking_model.named_estimators_['svr'],
    "RF":       stacking_model.named_estimators_['rf'],
    "Stacking": stacking_model
}
# Метрики оцінки для оцінки моделей.
print("Оцінка моделей")
y_test_orig = np.expm1(y_test)

for name, model in models.items():
    y_pred_log  = model.predict(X_test)
    y_pred_orig = np.expm1(y_pred_log)
    r2_log  = r2_score(y_test, y_pred_log)
    mae_log = mean_absolute_error(y_test, y_pred_log)
    r2_orig  = r2_score(y_test_orig, y_pred_orig)
    mae_orig = mean_absolute_error(y_test_orig, y_pred_orig)
    print(f"\n--- {name} ---")
    print(f"  R²  (log-простiр) : {r2_log:.4f}")
    print(f"  MAE (log-простiр) : {mae_log:.4f}")
    print(f"  R²  (оригiнал)    : {r2_orig:.4f}")
    print(f"  MAE (оригiнал)    : {mae_orig:.2f}")

# Графік 1: True vs Predicted
def plot_true_vs_predicted_orig(models, X_test, y_test_orig):
    for name, model in models.items():
        fig, ax = plt.subplots(figsize=(7, 6))
        fig.suptitle(
            u"Сурогатні моделі для функції Розенброка\n",
            fontsize=13
        )

        y_pred_log = model.predict(X_test)
        y_pred_orig = np.expm1(y_pred_log)

        # Визначаємо межі графіка на основі реальних і передбачених значень
        min_val = min(np.min(y_test_orig), np.min(y_pred_orig))
        max_val = max(np.max(y_test_orig), np.max(y_pred_orig))

        ax.scatter(y_test_orig, y_pred_orig, alpha=0.5, color='darkorange',
                   edgecolor='k', s=25)
        ax.plot([min_val, max_val], [min_val, max_val],
                color='red', linestyle='--', linewidth=2,
                label=u'Ідеальний прогноз')

        r2_o = r2_score(y_test_orig, y_pred_orig)
        mae_o = mean_absolute_error(y_test_orig, y_pred_orig)

        ax.set_title(
            u"Модель: {} \nR²={:.4f}   MAE={:.2f}".format(
                name, r2_o, mae_o
            ),
            fontsize=12
        )
        ax.set_xlabel(u'Дійсні значення', fontsize=11)
        ax.set_ylabel(u'Передбачені значення', fontsize=11)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)

        plt.tight_layout()
        plt.savefig(f"rosenbrock_true_vs_pred_orig_{name}.png", dpi=150, bbox_inches='tight')
        plt.show()


# Графік 2: порівняння у 3D просторі.
def plot_rosenbrock_surface_orig(stacking_model):
    x1_grid = np.linspace(-2, 2, 80)
    x2_grid = np.linspace(-2, 2, 80)
    X1, X2  = np.meshgrid(x1_grid, x2_grid)

    Z_true_orig = rosenbrock(X1, X2)

    grid_pts   = np.column_stack([X1.ravel(), X2.ravel()])
    Z_surr_log = stacking_model.predict(grid_pts)
    Z_surr_orig = np.expm1(Z_surr_log).reshape(X1.shape)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5),
                             subplot_kw={'projection': '3d'})
    fig.suptitle(
        u"Функція Розенброка: справжня проти сурогатної\n",
        fontsize=12
    )

    titles = [u"Справжня функція", u"Сурогатна модель"]
    cmaps  = ['plasma', 'viridis']

    for ax, Z, title, cmap in zip(axes, [Z_true_orig, Z_surr_orig], titles, cmaps):
        surf = ax.plot_surface(X1, X2, Z, cmap=cmap,
                               alpha=0.88, edgecolor='none')
        ax.set_title(title, fontsize=11)
        ax.set_xlabel(u'$x_1$')
        ax.set_ylabel(u'$x_2$')
        ax.set_zlabel(u'$f(x_1, x_2)$')
        fig.colorbar(surf, ax=ax, shrink=0.45)

    plt.tight_layout()
    plt.savefig("rosenbrock_surface_orig.png", dpi=150, bbox_inches='tight')
    plt.show()


plot_true_vs_predicted_orig(models, X_test, y_test_orig)
plot_rosenbrock_surface_orig(stacking_model)