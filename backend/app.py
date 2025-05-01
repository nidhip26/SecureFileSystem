from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime
from base64 import b64encode, b64decode
from io import BytesIO
import os
import psycopg2.extras
from psycopg2 import connect

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from utils.b2_upload import upload_file_to_b2

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# PostgreSQL connection
conn = connect("postgresql://filedb_octn_user:Sxey93nh4V69exU7wwM9IoxQ2HJ4wJ2A@dpg-d08pb095pdvs739ogma0-a.virginia-postgres.render.com/filedb_octn", sslmode='require')
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


@app.route('/upload', methods=['POST'])
def upload_file():
    sender_id = request.form.get('sender_id')
    recipient_username = request.form.get('recipient_username')
    file = request.files['file']

    if not sender_id or not recipient_username or not file:
        return jsonify({'error': 'Missing required fields'}), 400

    # Fetch recipient public key and ID
    cursor.execute("SELECT id, public_key FROM users WHERE username = %s", (recipient_username,))
    recipient = cursor.fetchone()
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404

    recipient_id = recipient['id']
    recipient_public_key = serialization.load_pem_public_key(
        recipient['public_key'].encode(), backend=default_backend()
    )

    # Generate AES key and IV
    aes_key = os.urandom(32)
    iv = os.urandom(16)

    # Encrypt file with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    file_data = file.read()
    pad_len = 16 - (len(file_data) % 16)
    file_data += bytes([pad_len]) * pad_len
    encrypted_file_data = encryptor.update(file_data) + encryptor.finalize()

    # Encrypt AES key with recipient's public RSA key
    encrypted_aes_key = recipient_public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

    # Upload encrypted file to B2
    encrypted_stream = BytesIO(encrypted_file_data)
    s3_key, file_id = upload_file_to_b2(encrypted_stream, file.filename)

    # Insert into files table
    cursor.execute("""
        INSERT INTO files (id, owner_id, filename, s3_key, encrypted_aes_key, iv, mime_type, size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        file_id,
        sender_id,
        file.filename,
        s3_key,
        b64encode(encrypted_aes_key).decode(),
        b64encode(iv).decode(),
        file.mimetype,
        len(file_data)
    ))

    # Insert into file_permissions to share file with recipient
    cursor.execute("INSERT INTO file_permissions (file_id, user_id) VALUES (%s, %s)", (file_id, recipient_id))
    conn.commit()

    return jsonify({'message': 'File uploaded and encrypted', 'file_id': file_id}), 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']

    # Bcrypt hash for password
    password_hash = bcrypt.generate_password_hash(password).decode()

    # RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Derive AES key from password
    salt = os.urandom(16)
    iv = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
    aes_key = kdf.derive(password.encode())

    # Encrypt the private key
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(private_bytes) % 16)
    padded_private_key = private_bytes + bytes([pad_len] * pad_len)
    encrypted_private_key = encryptor.update(padded_private_key) + encryptor.finalize()

    # Store user
    cursor.execute("""
        INSERT INTO users (username, password_hash, encrypted_private_key, public_key, aes_salt, aes_iv)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        username,
        password_hash,
        b64encode(encrypted_private_key).decode(),
        public_key.decode(),
        b64encode(salt).decode(),
        b64encode(iv).decode()
    ))
    conn.commit()

    return jsonify({"message": "User registered"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "public_key": user['public_key'],
                "encrypted_private_key": user['encrypted_private_key'],
                "aes_salt": user['aes_salt'],
                "aes_iv": user['aes_iv']
            }
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/users', methods=['GET'])
def get_users():
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    return jsonify(users), 200




if __name__ == '__main__':
    app.run(port=5000)
