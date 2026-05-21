import numpy as np
from scipy.integrate import solve_ivp
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from scipy.stats import qmc
import matplotlib.pyplot as plt
from sklearn.ensemble import StackingRegressor, RandomForestRegressor

alpha_e = 0.65    # швидкість зараження (безсимптомні)
alpha_i = 0.005   # швидкість зараження (симптомні)
gamma   = 0.001   # швидкість повторного зараження
eta_v   = 0.05    # ефективність вакцини
k       = 0.08    # швидкість появи симптомів
rho     = 0.1     # швидкість одужання безсимптомних
mu      = 0.02    # коефіцієнт смертності
q_e     = 0.0     # карантин (безсимптомні)
q_i     = 0.0     # карантин (симптомні)
v       = 0.0     # вакцинація

t0, te  = 0, 100  # проміжок часу
Y0      = [0.9998, 0.0001, 0.0001, 0.0, 0.0]

b_min, b_max = 0.05, 0.20

# 1 Права частина інтегралу
def seird_rhs(t, y, beta_t):
    S, E, I, R, D = y
    beta = beta_t(t)

    dS = -alpha_e*(1 - q_e)*S*E - alpha_i*(1 - q_i)*S*I + gamma*R - eta_v*v*S
    dE =  alpha_e*(1 - q_e)*S*E + alpha_i*(1 - q_i)*S*I - k*E - rho*E
    dI =  k*E - (beta + mu)*I
    dR =  beta*I + rho*E - gamma*R + eta_v*v*S
    dD =  mu*I
    return [dS, dE, dI, dR, dD]

# 2 β(t) на 4 підінтервалах
def make_beta(b, t0=0, te=100, n=4):
    edges = np.linspace(t0, te, n + 1)
    def beta_t(t):
        idx = np.searchsorted(edges[1:], t, side='right')
        idx = min(idx, n - 1)
        return b[idx]
    return beta_t

# 3 Обчислення інтегралу I(t)dt
def solve_seird_integral(b):
    beta_t = make_beta(b)
    sol = solve_ivp(
        fun=lambda t, y: seird_rhs(t, y, beta_t),
        t_span=(t0, te),
        y0=Y0,
        method='RK45',
        t_eval=np.linspace(t0, te, 500),
        rtol=1e-6,
        atol=1e-8
    )
    I_t = sol.y[2]
    psi = np.trapezoid(I_t, sol.t)
    return psi


n_total = 150  # 100 train + 50 test
n_train = 100
n_test = 50

np.random.seed(42)
sampler = qmc.LatinHypercube(d=4, seed=42)
X_all = qmc.scale(sampler.random(n=n_total), b_min, b_max)
y_all = np.array([solve_seird_integral(X_all[i]) for i in range(n_total)])
print(f"min={y_all.min():.4f}, max={y_all.max():.4f}, mean={y_all.mean():.4f}")

X_train, X_test, y_train, y_test = train_test_split(
    X_all, y_all, test_size=n_test, random_state=42
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
        SVR(kernel='rbf', C=100, epsilon=0.001, gamma='scale')
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

# 4 Метрики оцінки (R², MAE, RMSE, MAX_RE)
print("Оцінка моделі")

for name, model in models.items():
    y_pred  = model.predict(X_test)
    r2      = r2_score(y_test, y_pred)
    mae     = mean_absolute_error(y_test, y_pred)
    rmse    = np.sqrt(mean_squared_error(y_test, y_pred))
    maxe    = np.max(np.abs(y_pred - y_test))
    max_re  = np.max(np.abs(y_pred - y_test) / np.maximum(1, np.abs(y_test)))

    print(f"\n--- {name} ---")
    print(f"  R²      : {r2:.6f}")
    print(f"  MAE     : {mae:.6f}")
    print(f"  RMSE    : {rmse:.6f}")
    print(f"  MAXE    : {maxe:.6f}")
    print(f"  MAX_RE  : {max_re:.6f}")


# 5 Графік 1: SEIRD (базові параметри)
def plot_seird_dynamics():
    b_base  = [0.1, 0.1, 0.1, 0.1]
    beta_t  = make_beta(b_base)
    sol     = solve_ivp(
        fun=lambda t, y: seird_rhs(t, y, beta_t),
        t_span=(t0, te),
        y0=Y0,
        method='RK45',
        t_eval=np.linspace(t0, te, 500)
    )
    t_arr   = sol.t
    S, E, I, R, D = sol.y

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(t_arr, S, label='S — сприйнятливі',  color='steelblue',  linewidth=2)
    ax.plot(t_arr, E, label='E — інфіковані (без симптомів)', color='orange', linewidth=2)
    ax.plot(t_arr, I, label='I — хворі',          color='red',        linewidth=2)
    ax.plot(t_arr, R, label='R — одужали',         color='green',      linewidth=2)
    ax.plot(t_arr, D, label='D — померли',         color='black',      linewidth=2)
    ax.set_title(
        'Динаміка SEIRD моделі COVID-19\n'
        r'$\beta(t)=0.1$, $\alpha_e=0.65$, $\alpha_i=0.005$, $\mu=0.02$',
        fontsize=13
    )
    ax.set_xlabel('Час (дні)', fontsize=12)
    ax.set_ylabel('Частка населення', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("seird_dynamics.png", dpi=150, bbox_inches='tight')
    plt.show()

# 6 Графік 2: True vs Predicted
def plot_true_vs_predicted(models, X_test, y_test):
    min_val, max_val = y_test.min(), y_test.max()

    for name, model in models.items():
        fig, ax = plt.subplots(figsize=(7, 6))
        fig.suptitle(
            r'Сурогатні моделі SEIRD COVID-19',
            fontsize=13
        )

        y_pred = model.predict(X_test)
        ax.scatter(y_test, y_pred, alpha=0.5, color='royalblue',
                   edgecolor='k', s=25)
        ax.plot([min_val, max_val], [min_val, max_val],
                color='red', linestyle='--', linewidth=2,
                label='Ідеальний прогноз')

        ax.set_title(
            f'Модель: {name}\n'
            f'R²={r2_score(y_test, y_pred):.4f}   '
            f'MAE={mean_absolute_error(y_test, y_pred):.5f}',
            fontsize=12
        )
        ax.set_xlabel(r'Дійсні $\psi(b)$', fontsize=11)
        ax.set_ylabel(r'Передбачені $\hat{\psi}(b)$', fontsize=11)
        ax.legend()
        ax.grid(True, linestyle=':', alpha=0.6)

        plt.tight_layout()
        plt.savefig(f"seird_true_vs_pred_{name}.png", dpi=150, bbox_inches='tight')
        plt.show()

# 7 Графік 3: Вплив коефіцієнт інтенсивності лікування на кількість хворих.
def plot_beta_vs_integral():
    beta_vals = np.linspace(b_min, b_max, 30)
    psi_vals  = [solve_seird_integral([b, b, b, b]) for b in beta_vals]

    b_grid    = np.column_stack([beta_vals]*4)
    psi_surr  = stacking_model.predict(b_grid)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(beta_vals, psi_vals,  'b-o', linewidth=2, markersize=5,
            label=r'Точна модель $\psi(b)$')
    ax.plot(beta_vals, psi_surr,  'r--s', linewidth=2, markersize=5,
            label=r'Сурогат (Stacking) $\hat{\psi}(b)$')
    ax.set_title(
        r'Залежність $\psi(b)=\int I(t)\,dt$ від рівномірного $\beta$',
        fontsize=13
    )
    ax.set_xlabel(r'$\beta$ (рівень лікування, однаковий на всіх підінтервалах)', fontsize=11)
    ax.set_ylabel(r'$\psi(b) = \int_0^{100} I(t)\,dt$', fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig("seird_beta_vs_integral.png", dpi=150, bbox_inches='tight')
    plt.show()

plot_seird_dynamics()
plot_true_vs_predicted(models, X_test, y_test)
plot_beta_vs_integral()