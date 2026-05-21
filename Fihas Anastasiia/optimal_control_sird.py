import numpy as np
import matplotlib.pyplot as plt


def get_heaviside(t, tau):
    return 1.0 if t >= tau else 0.0

def delay(arr, i, tau, h):
    k = int(round(tau / h))
    j = i - k
    if j < 0:
        return 0.0
    return arr[j]

def optimal_control_sird(
    beta=1.5, gamma=0.8, mu=0.2,
    tau1=7, tau2=14, tau3=15,
    A1=5, A2=5, A3=5, A4=0.8,
    W1=105, W2=100000, W3=100,
    N=1000, S0=800, I0=200,
    t_max=100, h=0.1, max_iter=20
):

    t = np.arange(0, t_max + h, h)
    n = len(t)
    v1 = np.zeros(n)
    v2 = np.zeros(n)
    v3 = np.zeros(n)
    for _ in range(max_iter):
        S = np.zeros(n)
        I = np.zeros(n)
        R = np.zeros(n)
        D = np.zeros(n)
        dS_history = np.zeros(n)
        S[0] = S0 / N
        I[0] = I0 / N
        v1_old, v2_old, v3_old = v1.copy(), v2.copy(), v3.copy()

        def f(i, s, it, v1i, v2i, v3i):
            I_tau1 = delay(I, i, tau1, h)
            H1 = get_heaviside(t[i], tau1)
            dS_tau2 = delay(dS_history, i, tau2, h)
            dS_tau3 = delay(dS_history, i, tau3, h)
            inf = beta * s * I_tau1 * (1 - v2i) * H1
            dS = -inf - v1i * s
            dI = inf + gamma * dS_tau2 + mu * dS_tau3 - v3i * it
            dR = -gamma * dS_tau2 + v1i * s + v3i * it
            dD = -mu * dS_tau3
            return np.array([dS, dI, dR, dD])

        for i in range(n - 1):

            k1 = f(i, S[i], I[i], v1[i], v2[i], v3[i])
            k2 = f(i, S[i] + h*k1[0]/2, I[i] + h*k1[1]/2, v1[i], v2[i], v3[i])
            k3 = f(i, S[i] + h*k2[0]/2, I[i] + h*k2[1]/2, v1[i], v2[i], v3[i])
            k4 = f(i, S[i] + h*k3[0],   I[i] + h*k3[1],   v1[i], v2[i], v3[i])
            step = (h/6) * (k1 + 2*k2 + 2*k3 + k4)
            S[i+1] = max(S[i] + step[0], 0)
            I[i+1] = max(I[i] + step[1], 0)
            R[i+1] = max(R[i] + step[2], 0)
            D[i+1] = max(D[i] + step[3], 0)
            dS_history[i] = step[0]
        total = S + I + R + D
        total[total == 0] = 1
        S /= total
        I /= total
        R /= total
        D /= total
        psi1 = np.zeros(n)
        psi2 = np.zeros(n)
        psi3 = np.zeros(n)
        psi4 = np.zeros(n)
        psi3[-1] = -A2
        psi4[-1] = A3

        for i in range(n - 2, -1, -1):

            H1  = get_heaviside(t[i], tau1)
            H12 = get_heaviside(t[i], tau1 + tau2)
            H13 = get_heaviside(t[i], tau1 + tau3)
            I_tau1  = delay(I, i, tau1, h)
            I_tau12 = delay(I, i, tau1 + tau2, h)
            I_tau13 = delay(I, i, tau1 + tau3, h)
            S_tau2  = delay(S, i, tau2, h)
            S_tau3  = delay(S, i, tau3, h)
            chi1 = get_heaviside(t[i], tau1)
            chi2 = get_heaviside(t[i], tau2)
            chi3 = get_heaviside(t[i], tau3)
            chi12 = get_heaviside(t[i], tau1 + tau2)
            chi13 = get_heaviside(t[i], tau1 + tau3)
            term1 = psi1[i+1] * (-H1*(1-v2[i])*beta*I_tau1 - v1[i])
            term2 = chi2 * psi2[i] * (-gamma*(1-v2[i])*beta*I_tau12*H12 - v1[i]*gamma)
            term3 = chi3 * psi2[i] * (-mu*(1-v2[i])*beta*I_tau13*H13 - v1[i]*mu)
            term4 = chi2 * psi3[i] * (gamma*(1-v2[i])*beta*I_tau12*H12 + v1[i]*gamma)
            term5 = psi3[i] * v1[i]
            term6 = chi3 * psi4[i] * (mu*(1-v2[i])*beta*I_tau13*H13 + v1[i]*mu)
            dpsi1 = -(A4 + term1 + term2 + term3 + term4 + term5 + term6)
            term_psi21 = psi1[i+1]*chi1*(-beta*(1-v2[i])*S[i]*H1)
            term_psi22 = psi2[i]*chi1*beta*(1-v2[i])*S[i]*H1
            term_psi23 = psi2[i]*chi12*(-gamma*beta*S_tau2*(1-v2[i])*H12)
            term_psi24 = psi2[i]*chi13*(-mu*beta*S_tau3*(1-v2[i])*H13)
            term_psi25 = -psi2[i+1] * v3[i]
            term_psi26 = chi12*psi3[i]*gamma*beta*S_tau2*H12*(1-v2[i])
            term_psi27 = chi13*psi4[i]*mu*beta*S_tau3*H13*(1-v2[i])
            term_psi28 = psi3[i+1] * v3[i]
            dpsi2 = -(A1 + term_psi21 + term_psi22 + term_psi23 +
                      term_psi24 + term_psi25 + term_psi26 +
                      term_psi27 + term_psi28)
            psi1[i] = psi1[i+1] - h * dpsi1
            psi2[i] = psi2[i+1] - h * dpsi2
            psi3[i] = psi3[i+1]
            psi4[i] = psi4[i+1]
        v1_new = np.clip((psi1 - psi3) * S / W1, 0, 1)
        v2_new = np.clip(beta * S * I * (psi1 - psi2) / W2, 0, 1)
        v3_new = np.clip((psi2 - psi3) * I / W3, 0, 1)
        alpha = 0.6
        v1 = alpha * v1_old + (1 - alpha) * v1_new
        v2 = alpha * v2_old + (1 - alpha) * v2_new
        v3 = alpha * v3_old + (1 - alpha) * v3_new
    print("Результат:")
    print(f"S={S[-1]:.4f}, I={I[-1]:.4f}, R={R[-1]:.4f}, D={D[-1]:.4f}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9))
    ax1.plot(t, S*N, label='S — сприятливі', lw=2)
    ax1.plot(t, I*N, label='I — інфіковані', lw=2)
    ax1.plot(t, R*N, label='R — одужалі', lw=2)
    ax1.plot(t, D*N, label='D — померлі', lw=2)
    ax1.set_xlabel('Час (дні)')
    ax1.set_ylabel('Кількість осіб')
    ax1.set_title('SIRD-модель із запізненням та оптимальним керуванням')
    ax1.legend()
    ax1.grid(True)
    ax2.step(t, v1, where='post', label='$v_1$ — вакцинація', lw=2)
    ax2.step(t, v2, where='post', label='$v_2$ — карантин', lw=2)
    ax2.step(t, v3, where='post', label='$v_3$ — лікування', lw=2)
    ax2.set_xlabel('Час (дні)')
    ax2.set_ylabel('Інтенсивність керування')
    ax2.set_title('Оптимальні керуючі впливи')
    ax2.set_ylim(0, 1)
    ax2.legend()
    ax2.grid(True)
    plt.tight_layout()
    plt.show()
    return t, S, I, R, D, v1, v2, v3

optimal_control_sird()
