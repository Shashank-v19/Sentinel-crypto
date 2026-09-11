import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for
from tensorflow.keras.models import load_model
from encryption import encrypt_image
from decryption import decrypt_image
from metrics import calculate_entropy, npcr, uaci
import uuid
import hashlib

app = Flask(__name__)
# Ensure static upload directories exist
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("Loading Autoencoder model... This might take a moment.")
model = load_model("models/autoencoder.h5", compile=False)
encoder = model.layers[0]

# Route for Sender HTML
@app.route('/')
def sender_page():
    return render_template('sender.html')

# Route for Receiver HTML
@app.route('/receiver')
def receiver_page():
    return render_template('receiver.html')

# API for encryption
@app.route('/api/encrypt', methods=['POST'])
def api_encrypt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'})

    file = request.files['image']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Preprocess (Resize ONLY for the AI Model to get features)
    image_rz = cv2.resize(image, (32, 32))
    image_norm = image_rz / 255.0

    # Extract features using the 32x32 image
    features = model.predict(np.expand_dims(image_norm, axis=0))[0]

    # Generate unique ID for files (Also acts as our Cryptographic IV)
    session_id = uuid.uuid4().hex
    
    # Encrypt the ORIGINAL high-resolution image, not the resized one!
    encrypted = encrypt_image(image, features, session_id=session_id)
    
    # Save encrypted image
    enc_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_encrypted.png")
    cv2.imwrite(enc_path, encrypted)
    
    # Save original for NPCR/UACI comparison reference in the backend
    orig_path = os.path.join(UPLOAD_FOLDER, f"{session_id}_original.png")
    cv2.imwrite(orig_path, image)

    # Save features for the receiver to decrypt (Simulated secure key exchange)
    np.save(os.path.join(UPLOAD_FOLDER, f"{session_id}_features.npy"), features)

    # Metrics on the original image vs encrypted
    entropy = calculate_entropy(encrypted)
    n = npcr(image, encrypted)
    u = uaci(image, encrypted)

    # Calculate the exact x0 used for frontend formula display
    x0_base = float(np.sum(features)) % 1.0
    h_val = int(hashlib.sha256(session_id.encode()).hexdigest()[:8], 16)
    x0_salt = h_val / 4294967295.0
    x0_final = (x0_base + x0_salt) % 1.0
    if x0_final <= 0 or x0_final >= 1: 
        x0_final = 0.5

    return jsonify({
        'status': 'success',
        'encryptedUrl': f'/static/uploads/{session_id}_encrypted.png',
        'sessionId': session_id,
        'metrics': {
            'entropy': round(entropy, 4),
            'npcr': round(n, 4),
            'uaci': round(u, 4)
        },
        'formulaData': {
            'x0': round(x0_final, 8)
        }
    })

# API for decryption
@app.route('/api/decrypt', methods=['POST'])
def api_decrypt():
    if 'image' not in request.files:
         return jsonify({'error': 'No encrypted image uploaded'})
    
    sessionId = request.form.get('sessionId')
    if not sessionId:
        return jsonify({'error': 'No sessionId provided'})

    file = request.files['image']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    # the image was read as exactly what it is, we need it to decrypt properly.
    # CV2 imdecode might mess with channels, we read in color.
    encrypted = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Load features (the key)
    feat_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_features.npy")
    if not os.path.exists(feat_path):
         return jsonify({'error': 'Decryption key (features) missing for this session'})
    
    features = np.load(feat_path)

    # Decrypt
    decrypted = decrypt_image(encrypted, features, session_id=sessionId)

    # Save decrypted
    dec_path = os.path.join(UPLOAD_FOLDER, f"{sessionId}_decrypted.png")
    cv2.imwrite(dec_path, decrypted)

    return jsonify({
        'status': 'success',
        'decryptedUrl': f'/static/uploads/{sessionId}_decrypted.png'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
