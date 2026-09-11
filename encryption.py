import numpy as np
import cv2
from chaos import logistic_map
import hashlib

def encrypt_image(image, features, session_id=None):
    flat = image.flatten()

    # Dynamic x0 from features
    x0 = float(np.sum(features)) % 1.0

    if session_id:
        # Use session_id to create an Initialization Vector (IV)
        h_val = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16) 
        x0_salt = h_val / 4294967295.0
        x0 = (x0 + x0_salt) % 1.0

    if x0 <= 0 or x0 >= 1:
        x0 = 0.5

    # Chaos sequence
    chaos = logistic_map(len(flat), x0=x0)
    chaos = (chaos * 255).astype(np.uint8)

    # CNN feature key
    key = features.flatten()
    key = (key * 255).astype(np.uint8)

    # Resize key
    key = np.resize(key, flat.shape)

    # Hybrid key
    final_key = np.bitwise_xor(chaos, key)

    # Diffusion (XOR)
    encrypted = np.bitwise_xor(flat, final_key)

    return encrypted.reshape(image.shape)