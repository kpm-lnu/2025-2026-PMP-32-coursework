import math

def edge_energy(p1, p2, k_up, k_down):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    flight = math.sqrt(dx * dx + dy * dy)  
    if dz > 0:
        return flight + k_up * dz
    else:
        return flight + k_down * (-dz)
