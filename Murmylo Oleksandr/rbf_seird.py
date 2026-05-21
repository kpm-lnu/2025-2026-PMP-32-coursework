import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import solve_ivp
from scipy.spatial.distance import cdist
from scipy.optimize import minimize_scalar
import time

PARAMS = {
    'alpha_e': 0.65,
    'alpha_i': 0.005,
    'k': 0.05,
    'rho': 0.08,
    'mu': 0.02,
}
Y0 = [0.9998, 0.0001, 0.0001, 0.0, 0.0]


def seird_rhs(t, y, alpha_e, alpha_i, gamma, k, rho, beta, mu):
    S, E, I, R, D = y
    dS = -alpha_e * S * E - alpha_i * S * I + gamma * R
    dE = alpha_e * S * E + alpha_i * S * I - k * E - rho * E
    dI = k * E - beta * I - mu * I
    dR = beta * I + rho * E - gamma * R
    dD = mu * I
    return [dS, dE, dI, dR, dD]


def seird_lockdown_rhs(t, y, gamma, k, rho, beta, mu):
    S, E, I, R, D = y
    alpha_e = 0.1 if 15 < t <= 30 else 0.65
    alpha_i = 0.005
    dS = -alpha_e * S * E - alpha_i * S * I + gamma * R
    dE = alpha_e * S * E + alpha_i * S * I - k * E - rho * E
    dI = k * E - beta * I - mu * I
    dR = beta * I + rho * E - gamma * R
    dD = mu * I
    return [dS, dE, dI, dR, dD]


def solve_seird(beta, gamma):
    return solve_ivp(
        seird_rhs, (0, 150), Y0,
        args=(PARAMS['alpha_e'], PARAMS['alpha_i'], gamma,
              PARAMS['k'], PARAMS['rho'], beta, PARAMS['mu']),
        method='RK45', max_step=0.5
    )


def solve_seird_lockdown(beta, gamma):
    return solve_ivp(
        seird_lockdown_rhs, (0, 150), Y0,
        args=(gamma, PARAMS['k'], PARAMS['rho'], beta, PARAMS['mu']),
        method='RK45', max_step=0.5
    )


def compute_psi(beta, gamma, lockdown=False):
    sol = solve_seird_lockdown(beta, gamma) if lockdown else solve_seird(beta, gamma)
    return np.trapezoid(sol.y[2], sol.t)


def rbf_gaussian(r, eps):     return np.exp(-(eps * r) ** 2)


def rbf_multiquadric(r, eps): return np.sqrt(r ** 2 + eps ** 2)


def rbf_thin_plate(r):
    result = np.zeros_like(r)
    mask = r > 1e-8
    result[mask] = r[mask] ** 2 * np.log(r[mask])
    return result


def train_rbf(X_train, y_train, eps=1.0, rbf_type='gaussian'):
    D = cdist(X_train, X_train)
    if rbf_type == 'gaussian':
        Phi = rbf_gaussian(D, eps)
    elif rbf_type == 'multiquadric':
        Phi = rbf_multiquadric(D, eps)
    else:
        Phi = rbf_thin_plate(D)
    Phi += 1e-8 * np.eye(len(X_train))
    return np.linalg.solve(Phi, y_train)


def predict_rbf(X_new, X_train, weights, eps=1.0, rbf_type='gaussian'):
    D = cdist(X_new, X_train)
    if rbf_type == 'gaussian':
        Phi = rbf_gaussian(D, eps)
    elif rbf_type == 'multiquadric':
        Phi = rbf_multiquadric(D, eps)
    else:
        Phi = rbf_thin_plate(D)
    return Phi @ weights


def rmse(a, b):   return np.sqrt(np.mean((a - b) ** 2))


def r2(a, b):     return 1 - np.sum((a - b) ** 2) / np.sum((a - np.mean(a)) ** 2)


def mae(a, b):    return np.mean(np.abs(a - b))


def max_re(a, b): return np.max(np.abs(a - b) / np.maximum(1.0, np.abs(a)))


def generate_grid(n, bounds):
    axes = [np.linspace(lo, hi, n) for lo, hi in bounds]
    return np.array([[x, y] for x in axes[0] for y in axes[1]])


BOUNDS = [(0.05, 0.20), (0.0, 0.005)]
EPS = 5.0
N = 6
RBF_TYPE = 'gaussian'

print("=" * 55)
print("RBF-сурогат для SEIRD моделі COVID-19")
print("=" * 55)

print("\nГрафік 1: три сценарії SEIRD...")

sol1 = solve_seird(beta=0.1, gamma=0.0)
sol2 = solve_seird(beta=0.1, gamma=0.001)
sol3 = solve_seird_lockdown(beta=0.1, gamma=0.001)

labels = ['S', 'E', 'I', 'R', 'D']
colors = ['blue', 'cyan', 'red', 'green', 'black']

scenarios = [
    (sol1, 'Сценарій 1: довічний імунітет (γ=0)', 'seird_g1_1_dynamika.png'),
    (sol2, 'Сценарій 2: повторне зараження (γ=0.001)', 'seird_g1_2_dynamika.png'),
    (sol3, 'Сценарій 3: локдаун з 16 по 30 день', 'seird_g1_3_dynamika.png')
]

for sol, title, filename in scenarios:
    plt.figure(figsize=(6, 4))
    for i, (lbl, col) in enumerate(zip(labels, colors)):
        plt.plot(sol.t, sol.y[i], label=lbl, color=col)
    plt.xlabel('t (дні)')
    plt.ylabel('Частка населення')
    plt.title(title, fontsize=10)
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.show()
    plt.close()

psi1 = compute_psi(0.1, 0.0)
psi2 = compute_psi(0.1, 0.001)
psi3 = compute_psi(0.1, 0.001, lockdown=True)
print(f"  psi (довічний імунітет):    {psi1:.4f}")
print(f"  psi (повторне зараження):   {psi2:.4f}")
print(f"  psi (локдаун):              {psi3:.4f}")

print("\nНавчання RBF-сурогату (6x6=36 точок)...")
X_train = generate_grid(N, BOUNDS)
y_train = np.array([compute_psi(b[0], b[1]) for b in X_train])
weights = train_rbf(X_train, y_train, EPS, RBF_TYPE)

X_test = generate_grid(20, BOUNDS)
y_true = np.array([compute_psi(b[0], b[1]) for b in X_test])
y_pred = predict_rbf(X_test, X_train, weights, EPS, RBF_TYPE)

err_rmse = rmse(y_true, y_pred)
err_r2 = r2(y_true, y_pred)
err_mae = mae(y_true, y_pred)
err_maxre = max_re(y_true, y_pred)
print(f"  RMSE   = {err_rmse:.6f}")
print(f"  R2     = {err_r2:.6f}")
print(f"  MAE    = {err_mae:.6f}")
print(f"  MAX_RE = {err_maxre * 100:.4f}%")

print("\nГрафік 2: діаграми розсіювання RBF vs True...")

rbf_types = ['gaussian', 'multiquadric', 'thin_plate']
rbf_labels = ['Gaussian', 'Multiquadric', 'Thin Plate']
rbf_files = ['seird_g2_1_surrogat.png', 'seird_g2_2_surrogat.png', 'seird_g2_3_surrogat.png']

for rtype, rlabel, filename in zip(rbf_types, rbf_labels, rbf_files):
    w = train_rbf(X_train, y_train, EPS, rtype)
    yp = predict_rbf(X_test, X_train, w, EPS, rtype)
    r2_val = r2(y_true, yp)
    mae_val = mae(y_true, yp)

    lims = [min(y_true.min(), yp.min()) * 0.97,
            max(y_true.max(), yp.max()) * 1.03]

    plt.figure(figsize=(6, 5))
    plt.plot(lims, lims, 'r--', linewidth=1.5, label='Ідеальний прогноз', zorder=1)
    sc = plt.scatter(y_true, yp, c=np.abs(y_true - yp),
                     cmap='YlOrRd', s=25, alpha=0.8, edgecolors='none', zorder=2)
    plt.colorbar(sc, label='|похибка|', shrink=0.85)

    plt.xlim(lims)
    plt.ylim(lims)
    plt.xlabel('Дійсні значення ψ', fontsize=10)
    plt.ylabel('Передбачені значення ψ', fontsize=10)
    plt.title(f'Сурогатна модель: {rlabel}\n(ψ = ∫I(t)dt) | R²={r2_val:.4f} MAE={mae_val:.4f}', fontsize=11)
    plt.legend(fontsize=8, loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.gca().set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.show()
    plt.close()

print("\nГрафік 3: збіжність...")
n_values = [3, 4, 5, 6, 7, 8, 10]
rmse_vals = []
for n in n_values:
    Xt = generate_grid(n, BOUNDS)
    yt = np.array([compute_psi(b[0], b[1]) for b in Xt])
    w = train_rbf(Xt, yt, EPS, RBF_TYPE)
    yp = predict_rbf(X_test, Xt, w, EPS, RBF_TYPE)
    e = rmse(y_true, yp)
    rmse_vals.append(e)
    print(f"  {n}x{n}={n * n} точок -> RMSE={e:.6f}")

plt.figure(figsize=(6, 4))
plt.plot([n * n for n in n_values], rmse_vals, 'o-', color='steelblue', linewidth=2)
plt.xlabel('Кількість точок')
plt.ylabel('RMSE')
plt.title('Збіжність RBF-сурогату (SEIRD)')
plt.grid(True, alpha=0.4)
plt.yscale('log')
plt.tight_layout()
plt.savefig('seird_g3_zbizhist.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("\nГрафік 4: 3D-поверхні True vs Surrogate...")

beta_v = np.linspace(BOUNDS[0][0], BOUNDS[0][1], 30)
gamma_v = np.linspace(BOUNDS[1][0], BOUNDS[1][1], 30)
BB, GG = np.meshgrid(beta_v, gamma_v)

pts_grid = np.column_stack([BB.ravel(), GG.ravel()])
psi_true_3d = np.array([compute_psi(b[0], b[1]) for b in pts_grid]).reshape(30, 30)
psi_pred_3d = predict_rbf(pts_grid, X_train, weights, EPS, RBF_TYPE).reshape(30, 30)

vmin = min(psi_true_3d.min(), psi_pred_3d.min())
vmax = max(psi_true_3d.max(), psi_pred_3d.max())

fig = plt.figure(figsize=(7, 5))
ax1 = fig.add_subplot(1, 1, 1, projection='3d')
surf1 = ax1.plot_surface(BB, GG, psi_true_3d,
                         cmap='viridis', vmin=vmin, vmax=vmax,
                         linewidth=0, antialiased=True, alpha=0.92)
ax1.set_xlabel('β (beta)', fontsize=9, labelpad=6)
ax1.set_ylabel('γ (gamma)', fontsize=9, labelpad=6)
ax1.set_zlabel('ψ', fontsize=10)
ax1.set_title('Функція ψ(β, γ): Справжня функція', fontsize=11, fontweight='bold')
ax1.view_init(elev=25, azim=-55)
fig.colorbar(surf1, ax=ax1, shrink=0.5, label='ψ')
plt.tight_layout()
plt.savefig('seird_g4_1_typy_true.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

fig = plt.figure(figsize=(7, 5))
ax2 = fig.add_subplot(1, 1, 1, projection='3d')
surf2 = ax2.plot_surface(BB, GG, psi_pred_3d,
                         cmap='viridis', vmin=vmin, vmax=vmax,
                         linewidth=0, antialiased=True, alpha=0.92)
ax2.set_xlabel('β (beta)', fontsize=9, labelpad=6)
ax2.set_ylabel('γ (gamma)', fontsize=9, labelpad=6)
ax2.set_zlabel('ψ', fontsize=10)
ax2.set_title(f'Функція ψ(β, γ): Сурогатна модель\n(Gaussian RBF, ε={EPS}, {N}×{N} точок)', fontsize=11,
              fontweight='bold')
ax2.view_init(elev=25, azim=-55)
fig.colorbar(surf2, ax=ax2, shrink=0.5, label='ψ')
plt.tight_layout()
plt.savefig('seird_g4_2_typy_surrogate.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("\nОптимізація beta (gamma=0.001)...")
GAMMA_OPT = 0.001

t0 = time.time()
res_fine = minimize_scalar(
    lambda beta: compute_psi(beta, GAMMA_OPT),
    bounds=(0.05, 0.20), method='bounded'
)
t_fine = time.time() - t0
beta_opt_fine = res_fine.x
psi_opt_fine = res_fine.fun

t0 = time.time()
res_sm = minimize_scalar(
    lambda beta: predict_rbf(
        np.array([[beta, GAMMA_OPT]]), X_train, weights, EPS, RBF_TYPE
    )[0],
    bounds=(0.05, 0.20), method='bounded'
)
t_sm = time.time() - t0
beta_opt_sm = res_sm.x
psi_opt_sm = predict_rbf(np.array([[beta_opt_sm, GAMMA_OPT]]), X_train, weights, EPS, RBF_TYPE)[0]
psi_opt_sm_check = compute_psi(beta_opt_sm, GAMMA_OPT)

print(f"\n  {'Параметр':<30} {'Fine model':>12} {'Сурогат':>12}")
print(f"  {'-' * 55}")
print(f"  {'Оптимальне beta*':<30} {beta_opt_fine:>12.4f} {beta_opt_sm:>12.4f}")
print(f"  {'psi (сурогат/fine)':<30} {psi_opt_fine:>12.4f} {psi_opt_sm:>12.4f}")
print(f"  {'psi (верифікація fine)':<30} {'—':>12} {psi_opt_sm_check:>12.4f}")
print(f"  {'Час оптимізації':<30} {t_fine * 1000:>11.1f}мс {t_sm * 1000:>11.1f}мс")
rel_err = abs(psi_opt_fine - psi_opt_sm_check) / abs(psi_opt_fine) * 100
print(f"  {'Відносна похибка psi':<30} {'—':>12} {rel_err:>11.2f}%")

print("\nГрафік 5: порівняння початкового і оптимального...")
sol_init = solve_seird(beta=0.1, gamma=GAMMA_OPT)
sol_fine = solve_seird(beta=beta_opt_fine, gamma=GAMMA_OPT)
sol_sm = solve_seird(beta=beta_opt_sm, gamma=GAMMA_OPT)
psi_init = compute_psi(0.1, GAMMA_OPT)

plt.figure(figsize=(6, 4))
plt.plot(sol_init.t, sol_init.y[2], 'k-',
         label=f'Початкове β=0.10\nψ={psi_init:.3f}')
plt.plot(sol_fine.t, sol_fine.y[2], 'r--',
         label=f'Fine model β={beta_opt_fine:.3f}\nψ={psi_opt_fine:.3f}')
plt.plot(sol_sm.t, sol_sm.y[2], 'b:',
         label=f'Сурогат β={beta_opt_sm:.3f}\nψ={psi_opt_sm_check:.3f}')
plt.xlabel('t (дні)')
plt.ylabel('I(t)')
plt.title('Динаміка I(t): початкове vs оптимальне')
plt.legend(fontsize=8)
plt.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig('seird_g5_1_optym_dynamics.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

plt.figure(figsize=(6, 4))
models = ['Початкове\nβ=0.10',
          f'Fine model\nβ={beta_opt_fine:.3f}',
          f'Сурогат\nβ={beta_opt_sm:.3f}']
psi_vals = [psi_init, psi_opt_fine, psi_opt_sm_check]
colors_bar = ['gray', 'red', 'blue']
bars = plt.bar(models, psi_vals, color=colors_bar, alpha=0.7)
plt.ylabel('ψ = ∫I(t)dt')
plt.title('Порівняння цільової функції')
for i, v in enumerate(psi_vals):
    plt.text(i, v + (max(psi_vals) * 0.02), f'{v:.3f}', ha='center', fontsize=10)
plt.grid(True, alpha=0.4, axis='y')
plt.tight_layout()
plt.savefig('seird_g5_2_optym_bars.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

print("\nВсе готово!")