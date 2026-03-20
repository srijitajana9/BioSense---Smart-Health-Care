# utils.py
import numpy as np
from sklearn.datasets import load_breast_cancer

rng = np.random.default_rng(42)

# --- Simulated Encryption (adds random noise for privacy) ---
def encrypt_array(arr, noise_scale=1e-3):
    noise = np.random.normal(loc=0.0, scale=noise_scale, size=arr.shape)
    encrypted = arr + noise
    print("[SimEnc] Original array:", arr)
    print("[SimEnc] Encrypted (noisy) array:", encrypted)
    return encrypted

def decrypt_array(arr):
    # No real decryption needed for simulated encryption
    return arr

def encrypt_vector(vec, noise_scale=1e-3):
    noise = np.random.normal(loc=0.0, scale=noise_scale, size=vec.shape)
    encrypted = vec + noise
    print("[SimEnc] Original vector:", vec)
    print("[SimEnc] Encrypted (noisy) vector:", encrypted)
    return encrypted

def decrypt_vector(vec):
    return vec

def _pick(X, y, mask, n):
    idx = np.where(mask)[0]
    idx = rng.choice(idx, size=min(n, len(idx)), replace=False)
    return X[idx], y[idx]

def load_partition(idx: int, non_iid: bool = True):
    """
    idx: 0 -> client A (benign-heavy)
    idx: 1 -> client B (malignant-heavy)
    idx: 2 -> client C (mixed + slight noise)
    non_iid=True gives heterogeneous splits good for FL demos
    """
    X, y = load_breast_cancer(return_X_y=True)
    n_total = len(y)

    if not non_iid:
        # simple equal contiguous split (IID-ish)
        n = n_total // 3
        start, end = idx * n, (idx + 1) * n if idx < 2 else n_total
        return X[start:end], y[start:end]

    # --- Non-IID recipe ---
    # target sizes per client (you can tweak)
    nA, nB, nC = 140, 140, 140

    benign = (y == 0)   # class 0
    malign = (y == 1)   # class 1

    if idx == 0:
        # Client A: 80% benign, 20% malignant
        Xa0, ya0 = _pick(X, y, benign, int(0.8 * nA))
        Xa1, ya1 = _pick(X, y, malign, int(0.2 * nA))
        XA = np.vstack([Xa0, Xa1])
        yA = np.concatenate([ya0, ya1])
        return XA, yA

    if idx == 1:
        # Client B: 80% malignant, 20% benign
        Xb1, yb1 = _pick(X, y, malign, int(0.8 * nB))
        Xb0, yb0 = _pick(X, y, benign, int(0.2 * nB))
        XB = np.vstack([Xb1, Xb0])
        yB = np.concatenate([yb1, yb0])
        return XB, yB

    # idx == 2
    # Client C: balanced + tiny Gaussian noise (domain shift)
    Xc0, yc0 = _pick(X, y, benign, int(0.5 * nC))
    Xc1, yc1 = _pick(X, y, malign, int(0.5 * nC))
    XC = np.vstack([Xc0, Xc1])
    yC = np.concatenate([yc0, yc1])

    # slight noise to simulate different device/site
    noise = rng.normal(loc=0.0, scale=0.05, size=XC.shape)
    XC_noisy = XC + noise
    return XC_noisy, yC
