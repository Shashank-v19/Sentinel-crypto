import numpy as np

def logistic_map(size, x0=0.5, r=3.99):
    seq = []
    x = x0
    for i in range(size):
        x = r * x * (1 - x)
        seq.append(x)
    return np.array(seq)