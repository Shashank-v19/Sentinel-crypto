import numpy as np
from chaos import logistic_map
import hashlib

def decrypt_image(encrypted, features, session_id=None):
    flat = encrypted.flatten()

    # Dynamic x0 from features
    x0 = float(np.sum(features)) % 1.0

    if session_id:
        # Reproduce the Initialization Vector using the session_id
        h_val = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16) 
        x0_salt = h_val / 4294967295.0
        x0 = (x0 + x0_salt) % 1.0

    if x0 <= 0 or x0 >= 1:
        x0 = 0.5

    chaos = logistic_map(len(flat), x0=x0)
    chaos = (chaos * 255).astype(np.uint8)

    key = features.flatten()
    key = (key * 255).astype(np.uint8)
    key = np.resize(key, flat.shape)

    final_key = np.bitwise_xor(chaos, key)

    decrypted = np.bitwise_xor(flat, final_key)

    return decrypted.reshape(encrypted.shape)