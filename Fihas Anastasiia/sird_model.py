import numpy as np
import matplotlib.pyplot as plt

def solve_sird(beta, gamma, mu, tau1, tau2, tau3, N, S0, I0, t_max=100, h=0.1):
    t = np.arange(0, t_max, h)
    steps = len(t)
    S, I, R, D = np.zeros(steps), np.zeros(steps), np.zeros(steps), np.zeros(steps)
    ds_dt_history = np.zeros(steps)
    S[0], I[0], R[0], D[0] = S0, I0, 0, 0
    
    def get_past(n, arr, tau):
        if tau <= 1e-5: 
            return arr[n]
        idx = n - int(tau / h)
        if idx >= 0:
            return arr[idx]
        else: return arr[0]
        
    for i in range(steps - 1):
        curr_S, curr_I = S[i], I[i]
        def equations(idx, s_v, i_v, current_t):
            s_v = s_v
            i_v = i_v
            if tau1 > 0:
                I_p = get_past(idx, I, tau1)
                if  current_t >= tau1:
                    H1=1
                else: H1=0
                inf_rate = beta * s_v * (I_p / N) * H1
            else:
                inf_rate = beta * s_v * (i_v / N)
            if tau2 > 0 and tau3 > 0:
                ds_tau2 = get_past(idx, ds_dt_history, tau2)
                ds_tau3 = get_past(idx, ds_dt_history, tau3)
                rec_rate = -gamma * ds_tau2
                det_rate = -mu * ds_tau3
            else:
                rec_rate = gamma * i_v
                det_rate = mu * i_v
                
            return np.array([
                -inf_rate,
                inf_rate - rec_rate - det_rate,
                rec_rate,
                det_rate
            ])
        k1 = equations(i, curr_S, curr_I, t[i])
        k2 = equations(i, curr_S + h*k1[0]/2, curr_I + h*k1[1]/2, t[i] + h/2)
        k3 = equations(i, curr_S + h*k2[0]/2, curr_I + h*k2[1]/2, t[i] + h/2)
        k4 = equations(i, curr_S + h*k3[0], curr_I + h*k3[1], t[i] + h)
        delta = (h / 6) * (k1 + 2*k2 + 2*k3 + k4)
        S[i+1] = S[i] + delta[0]
        I[i+1] = I[i] + delta[1]
        R[i+1] = R[i] + delta[2]
        D[i+1] = D[i] + delta[3]
        ds_dt_history[i] = delta[0] / h
    return t, S, I, R, D
# t, S, I, R, D = solve_sird(beta=0.4, 
# gamma=0.99, 
# mu=0.01, 
# tau1=6, 
# tau2=19, 
# tau3=20, 
# N=1000, 
# S0=999, 
# I0=1)
b=1.5
t, S, I, R, D = solve_sird(b, 0.98, 0.02, 0, 0, 0, 1000, 999, 1)
plt.figure(figsize=(10,6))
plt.plot(t,S,label='Сприятливі')
plt.plot(t,I,label='Інфіковані')
plt.plot(t,R,label='Одужалі')
plt.plot(t,D,label='Померлі')
plt.legend()
plt.xlabel('Час (дні)')
plt.ylabel('Кількість людей')
plt.title('SIRD-модель')
plt.grid()
plt.show()
