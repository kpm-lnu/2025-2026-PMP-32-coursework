import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
from mpl_toolkits.mplot3d import Axes3D


def rosenbrock(x, y):
    return (1 - x)**2 + 100 * (y - x**2)**2

def rastrigin(x, y):
    A = 10
    return (A * 2 +
            (x**2 - A * np.cos(2 * np.pi * x)) +
            (y**2 - A * np.cos(2 * np.pi * y)))

def himmelblau(x, y):
    return (x**2 + y - 11)**2 + (x + y**2 - 5)**2


def rbf_gaussian(r, eps):
    return np.exp(-(eps * r)**2)

def rbf_multiquadric(r, eps):
    return np.sqrt(r**2 + eps**2)

def rbf_thin_plate(r):
    result = np.zeros_like(r)
    mask = r > 1e-8
    result[mask] = r[mask]**2 * np.log(r[mask])
    return result


def generate_grid(n, x_min, x_max, y_min, y_max):
    x = np.linspace(x_min, x_max, n)
    y = np.linspace(y_min, y_max, n)
    X, Y = np.meshgrid(x, y)
    return np.column_stack([X.ravel(), Y.ravel()])

def compute_distances(A, B):
    return cdist(A, B)

def train_rbf(X_train, y_train, eps=1.0, rbf_type='gaussian'):
    D = compute_distances(X_train, X_train)
    if rbf_type == 'gaussian':
        Phi = rbf_gaussian(D, eps)
    elif rbf_type == 'multiquadric':
        Phi = rbf_multiquadric(D, eps)
    elif rbf_type == 'tps':
        Phi = rbf_thin_plate(D)
    else:
        raise ValueError("Невідомий тип RBF")
    Phi += 1e-8 * np.eye(len(X_train))
    return np.linalg.solve(Phi, y_train)

def predict_rbf(X_new, X_train, weights, eps=1.0, rbf_type='gaussian'):
    D = compute_distances(X_new, X_train)
    if rbf_type == 'gaussian':
        Phi = rbf_gaussian(D, eps)
    elif rbf_type == 'multiquadric':
        Phi = rbf_multiquadric(D, eps)
    elif rbf_type == 'tps':
        Phi = rbf_thin_plate(D)
    else:
        raise ValueError("Невідомий тип RBF")
    return Phi @ weights

def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred)**2))

def mae(y_true, y_pred):
    return np.mean(np.abs(y_true - y_pred))

def r2_score(y_true, y_pred):
    return 1 - np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2)



plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 120,
})

SCATTER_COLOR = '#d4a017'
IDEAL_COLOR   = '#e63946'
CMAP = 'viridis'


EPS      = 1.0
N        = 6
RBF_TYPE = 'gaussian'
x_min, x_max = -2, 2
y_min, y_max = -2, 2

print("=" * 55)
print("  RBF-сурогат для функції Розенброка")
print("=" * 55)

print("Генерація навчальних точок...")
X_train = generate_grid(N, x_min, x_max, y_min, y_max)
y_train = rosenbrock(X_train[:, 0], X_train[:, 1])

print(f"Навчання RBF-сурогату ({N}x{N}={N*N} точок)...")
weights = train_rbf(X_train, y_train, EPS, RBF_TYPE)

n_test = 50
x_lin = np.linspace(x_min, x_max, n_test)
y_lin = np.linspace(y_min, y_max, n_test)
XX, YY = np.meshgrid(x_lin, y_lin)
Z_true = rosenbrock(XX, YY)

X_test    = np.column_stack([XX.ravel(), YY.ravel()])
Z_pred_g  = predict_rbf(X_test, X_train, weights, EPS, 'gaussian').reshape(XX.shape)

error_rmse = rmse(Z_true.ravel(), Z_pred_g.ravel())
error_r2   = r2_score(Z_true.ravel(), Z_pred_g.ravel())
error_mae  = mae(Z_true.ravel(), Z_pred_g.ravel())
error_maxre = np.max(np.abs(Z_true.ravel() - Z_pred_g.ravel()) /
                     (np.abs(Z_true.ravel()) + 1e-10)) * 100

print(f"  RMSE   = {error_rmse:.6f}")
print(f"  R²     = {error_r2:.6f}")
print(f"  MAE    = {error_mae:.6f}")
print(f"  MAX_RE = {error_maxre:.4f}%")


def scatter_plot(y_true_flat, y_pred_flat, title_model, r2, mae_val, filename):
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.suptitle("Сурогатні моделі для функції Розенброка", fontsize=12, y=1.01)

    ax.set_title(f"Модель: {title_model}\nR²={r2:.4f}   MAE={mae_val:.2f}", fontsize=11)

    vmin = min(y_true_flat.min(), y_pred_flat.min())
    vmax = max(y_true_flat.max(), y_pred_flat.max())

    ax.scatter(y_true_flat, y_pred_flat,
               c=SCATTER_COLOR, edgecolors='none', alpha=0.55, s=18, zorder=3)

    ax.plot([vmin, vmax], [vmin, vmax],
            color=IDEAL_COLOR, linestyle='--', linewidth=1.5,
            label='Ідеальний прогноз', zorder=4)

    ax.set_xlabel("Дійсні значення")
    ax.set_ylabel("Передбачені значення")
    ax.legend(fontsize=9)
    ax.set_xlim(vmin, vmax)
    ax.set_ylim(vmin, vmax)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.4)

    fig.tight_layout()
    fig.savefig(filename, bbox_inches='tight')
    return fig


def surface_3d_comparison(XX, YY, Z_true, Z_pred, title_model, filename):
    fig = plt.figure(figsize=(13, 5))
    fig.suptitle("Функція Розенброка: справжня проти сурогатної", fontsize=12, y=1.01)

    vmin = Z_true.min()
    vmax = Z_true.max()

    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    surf1 = ax1.plot_surface(XX, YY, Z_true,
                             cmap=CMAP, vmin=vmin, vmax=vmax,
                             linewidth=0, antialiased=True, alpha=0.92)
    ax1.set_title("Справжня функція", fontsize=11)
    ax1.set_xlabel("x₁", labelpad=6)
    ax1.set_ylabel("x₂", labelpad=6)
    ax1.set_zlabel("f", labelpad=6)
    fig.colorbar(surf1, ax=ax1, shrink=0.55, aspect=10, pad=0.1)

    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    surf2 = ax2.plot_surface(XX, YY, Z_pred,
                             cmap=CMAP, vmin=vmin, vmax=vmax,
                             linewidth=0, antialiased=True, alpha=0.92)
    ax2.set_title(f"Сурогатна модель\n({title_model})", fontsize=11)
    ax2.set_xlabel("x₁", labelpad=6)
    ax2.set_ylabel("x₂", labelpad=6)
    ax2.set_zlabel("f", labelpad=6)
    fig.colorbar(surf2, ax=ax2, shrink=0.55, aspect=10, pad=0.1)

    fig.tight_layout()
    fig.savefig(filename, bbox_inches='tight')
    return fig


def convergence_plot(filename):
    print("\nДослідження збіжності...")
    n_values  = [3, 4, 5, 6, 7, 8, 10]
    rmse_vals = []

    for n in n_values:
        X_tr = generate_grid(n, x_min, x_max, y_min, y_max)
        y_tr = rosenbrock(X_tr[:, 0], X_tr[:, 1])
        w    = train_rbf(X_tr, y_tr, EPS, RBF_TYPE)
        y_p  = predict_rbf(X_test, X_tr, w, EPS, RBF_TYPE)
        err  = rmse(Z_true.ravel(), y_p)
        rmse_vals.append(err)
        print(f"  {n}x{n}={n*n} точок -> RMSE={err:.6f}")

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot([n*n for n in n_values], rmse_vals,
            'o-', color='#2196F3', linewidth=2, markersize=7)
    ax.set_xlabel("Кількість точок навчання", fontsize=11)
    ax.set_ylabel("RMSE", fontsize=11)
    ax.set_title("Збіжність RBF моделі", fontsize=13)
    ax.set_yscale("log")
    ax.grid(True, which='both', linestyle=':', alpha=0.5)
    fig.tight_layout()
    fig.savefig(filename, bbox_inches='tight')
    return fig


def rbf_comparison_scatters():
    print("\nПорівняння різних типів RBF-ядер...")
    print(f"  {'Модель':<22} {'RMSE':>10} {'R²':>10} {'MAE':>10}")
    print("  " + "-" * 54)
    configs = [
        ('gaussian',    'Gaussian'),
        ('multiquadric','Multiquadric'),
        ('tps',         'Thin Plate Spline'),
    ]
    figs = []
    for rbf_t, title in configs:
        w     = train_rbf(X_train, y_train, EPS, rbf_t)
        y_p   = predict_rbf(X_test, X_train, w, EPS, rbf_t)
        r2    = r2_score(Z_true.ravel(), y_p)
        mae_v = mae(Z_true.ravel(), y_p)
        err   = rmse(Z_true.ravel(), y_p)
        print(f"  {title:<22} {err:>10.6f} {r2:>10.6f} {mae_v:>10.6f}")

        fname = f"rbf_scatter_{rbf_t}.png"
        fig = scatter_plot(Z_true.ravel(), y_p, title, r2, mae_v, fname)
        figs.append(fig)
    return figs


print("\nГрафік 1: 3D поверхні Розенброка (справжня vs сурогатна)...")
fig1 = surface_3d_comparison(XX, YY, Z_true, Z_pred_g,
                             'RBF Gaussian',
                             'rbf_3d_comparison.png')

print("\nГрафік 2: збіжність RBF-моделі...")
fig2 = convergence_plot('rbf_convergence.png')

print("\nГрафік 3–5: порівняння scatter для кожного типу RBF...")
figs_rbf = rbf_comparison_scatters()

plt.show()
print("\nВсе готово!")