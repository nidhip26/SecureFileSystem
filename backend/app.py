from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from datetime import datetime
from base64 import b64encode, b64decode
from io import BytesIO
import os
import psycopg2.extras
from psycopg2 import connect
import uuid
from utils.b2_upload import download_file_from_b2
from flask import send_file
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.serialization import load_der_private_key

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
    sender_username = request.form.get('sender_username')
    recipient_username = request.form.get('recipient_username')
    file = request.files.get('file')

    print(f"Sender Username: {sender_username}")
    print(f"Recipient Username: {recipient_username}")
    print(f"File: {file}")

    if not sender_username or not recipient_username or not file:
        return jsonify({'error': 'Missing required fields'}), 400

    # Fetch sender info
    cursor.execute("SELECT id, public_key FROM users WHERE username = %s", (sender_username,))
    sender = cursor.fetchone()
    if not sender:
        return jsonify({'error': 'Sender not found'}), 404
    sender_id = sender['id']
    sender_public_key = serialization.load_pem_public_key(
        sender['public_key'].encode(), backend=default_backend()
    )

    # Fetch recipient info
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

    # Encrypt the file using AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    file_data = file.read()
    pad_len = 16 - (len(file_data) % 16)
    file_data += bytes([pad_len]) * pad_len
    encrypted_file_data = encryptor.update(file_data) + encryptor.finalize()

    # Upload to B2
    encrypted_stream = BytesIO(encrypted_file_data)
    s3_key, _ = upload_file_to_b2(encrypted_stream, file.filename)
    print(s3_key)
    file_id = str(uuid.uuid4())

    # Encrypt AES key for sender (to store in files table)
    encrypted_aes_key_for_sender = sender_public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

    # Insert into files table (encrypted key for sender only)
    cursor.execute("""
        INSERT INTO files (id, owner_id, filename, s3_key, encrypted_aes_key, iv, mime_type, size)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        file_id,
        sender_id,
        file.filename,
        s3_key,
        b64encode(encrypted_aes_key_for_sender).decode(),
        b64encode(iv).decode(),
        file.mimetype,
        len(file_data)
    ))

    # Encrypt AES key for recipient (for file_permissions)
    encrypted_aes_key_for_recipient = recipient_public_key.encrypt(
        aes_key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )

    # Insert into file_permissions (recipient only)
    cursor.execute("""
        INSERT INTO file_permissions (file_id, user_id, encrypted_aes_key)
        VALUES (%s, %s, %s)
    """, (
        file_id,
        recipient_id,
        b64encode(encrypted_aes_key_for_recipient).decode()
    ))

    conn.commit()

    return jsonify({'message': 'File uploaded and encrypted', 'file_id': file_id}), 200



@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    password = data['password']

    # Bcrypt hash for password
    password_hash = bcrypt.generate_password_hash(password).decode()
    print("password hash: ", password_hash)
    # RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    print("uncoded private key: ", private_key)
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("public key: ", public_key)

    # use PBKDF2 to derive AES key from password
    salt = os.urandom(16)
    iv = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
    aes_key = kdf.derive(password.encode())

    print("salt: ", salt)
    print("iv: ", iv)
    print("aes key", aes_key)
    # Encrypt the private key with aes key
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - (len(private_bytes) % 16)
    padded_private_key = private_bytes + bytes([pad_len] * pad_len)
    encrypted_private_key = encryptor.update(padded_private_key) + encryptor.finalize()

    # Store user in users table
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

from flask import Flask, request, jsonify

@app.route('/files', methods=['GET'])
def get_files():
    username = request.args.get('username')
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Get user ID
    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"error": "User not found"}), 404
    user_id = user['id']

    # Get accessible files
    cursor.execute("""
        SELECT f.id, f.filename, f.mime_type, f.size, f.s3_key
        FROM files f
        JOIN file_permissions fp ON f.id = fp.file_id
        WHERE fp.user_id = %s
    """, (user_id,))
    files = cursor.fetchall()

    # Return the list of files
    return jsonify(files), 200


@app.route('/file-content', methods=['POST'])
def get_file_content():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    file_id = data.get('file_id')

    if not username or not password or not file_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # Step 1: Get user info
    cursor.execute("SELECT id, encrypted_private_key, aes_salt, aes_iv FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_id = user['id']
    encrypted_private_key = b64decode(user['encrypted_private_key'])
    salt = b64decode(user['aes_salt'])
    iv = b64decode(user['aes_iv'])

    # Step 2: Derive AES key using PBKDF2
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
    aes_key = kdf.derive(password.encode())
    print(aes_key)

    # Step 3: Decrypt user's private key
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_private_key = decryptor.update(encrypted_private_key) + decryptor.finalize()
    pad_len = padded_private_key[-1]
    private_key_bytes = padded_private_key[:-pad_len]

    private_key = serialization.load_pem_private_key(private_key_bytes, password=None, backend=default_backend())

    # Step 4: Fetch encrypted AES key for this file from file_permissions
    cursor.execute("SELECT encrypted_aes_key FROM file_permissions WHERE file_id = %s AND user_id = %s", (file_id, user_id))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'No access to this file'}), 403

    encrypted_aes_key = b64decode(row['encrypted_aes_key'])

    # Step 5: Decrypt the AES key using RSA
    try:
        file_aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
    except Exception as e:
        return jsonify({'error': f'Decryption failed: {str(e)}'}), 500

    # Step 6: Fetch file metadata from files table
    cursor.execute("SELECT s3_key, iv FROM files WHERE id = %s", (file_id,))
    file_meta = cursor.fetchone()
    if not file_meta:
        return jsonify({'error': 'File not found'}), 404

    s3_key = file_meta['s3_key']
    file_iv = b64decode(file_meta['iv'])

    # Step 7: Download encrypted file from B2
    encrypted_data = download_file_from_b2(s3_key)

    # Step 8: Decrypt the file
    cipher = Cipher(algorithms.AES(file_aes_key), modes.CBC(file_iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
    pad_len = padded_data[-1]
    decrypted_data = padded_data[:-pad_len]

    # Step 9: Return the plaintext content (assumes text)
    return jsonify({"content": decrypted_data.decode('utf-8')}), 200


@app.route('/download/<file_id>', methods=['POST', 'OPTIONS'])
def download_file(file_id):
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    # Handle POST request
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            print("Failed to parse JSON data")
            return jsonify({'error': 'Missing or invalid JSON data'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        print(f"Processing download for user: {username}, file: {file_id}")
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
            
        # Step 1: Get user info
        cursor.execute("SELECT id, encrypted_private_key, aes_salt, aes_iv FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        user_id = user['id']
        encrypted_private_key = b64decode(user['encrypted_private_key'])
        salt = b64decode(user['aes_salt'])
        iv = b64decode(user['aes_iv'])
        
        # Step 2: Derive AES key from password
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
        aes_key = kdf.derive(password.encode())
        
        # Step 3: Decrypt AES-encrypted private key
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_private_key) + decryptor.finalize()
       
        # Improved private key handling
        private_key = None
        key_load_successful = False
        
        # Try loading directly first
        try:
            private_key = serialization.load_pem_private_key(
                decrypted_data, 
                password=None, 
                backend=default_backend()
            )
            key_load_successful = True
        except Exception as e1:
            print(f"Direct key load failed: {str(e1)}")
            
            # Look for PEM markers
            try:
                begin_marker = b"-----BEGIN PRIVATE KEY-----"
                end_marker = b"-----END PRIVATE KEY-----"
                
                begin_idx = decrypted_data.find(begin_marker)
                end_idx = decrypted_data.find(end_marker)
                
                if begin_idx >= 0 and end_idx > begin_idx:
                    key_data = decrypted_data[begin_idx:end_idx + len(end_marker)]
                    private_key = serialization.load_pem_private_key(
                        key_data, 
                        password=None, 
                        backend=default_backend()
                    )
                    key_load_successful = True
                else:
                    # Try RSA format
                    begin_rsa = b"-----BEGIN RSA PRIVATE KEY-----"
                    end_rsa = b"-----END RSA PRIVATE KEY-----"
                    
                    begin_idx = decrypted_data.find(begin_rsa)
                    end_idx = decrypted_data.find(end_rsa)
                    
                    if begin_idx >= 0 and end_idx > begin_idx:
                        key_data = decrypted_data[begin_idx:end_idx + len(end_rsa)]
                        private_key = serialization.load_pem_private_key(
                            key_data, 
                            password=None, 
                            backend=default_backend()
                        )
                        key_load_successful = True
            except Exception as e2:
                print(f"PEM extraction failed: {str(e2)}")
        
        if not key_load_successful or private_key is None:
            return jsonify({
                'error': 'Failed to decrypt private key. Invalid password or corrupted key.',
                'debug_info': f"Key decryption failed with {len(password)} character password"
            }), 400
            
        # Step 4: Get file permission
        cursor.execute(
            "SELECT encrypted_aes_key FROM file_permissions WHERE file_id = %s AND user_id = %s", 
            (file_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'No access to this file'}), 403
            
        encrypted_aes_key = b64decode(row['encrypted_aes_key'])
        
        try:
            file_aes_key = private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()), 
                    algorithm=hashes.SHA256(), 
                    label=None
                )
            )
        except Exception as e:
            print(f"Failed to decrypt file key: {str(e)}")
            return jsonify({'error': 'Failed to decrypt file key'}), 400
            
        # Step 5: Fetch file metadata
        cursor.execute("SELECT s3_key, iv, filename, mime_type FROM files WHERE id = %s", (file_id,))
        file_meta = cursor.fetchone()
        if not file_meta:
            return jsonify({'error': 'File not found'}), 404
            
        s3_key = file_meta['s3_key']
        file_iv = b64decode(file_meta['iv'])
        filename = file_meta['filename']
        mime_type = file_meta['mime_type']
        
        # Step 6: Download encrypted file from B2
        encrypted_data = download_file_from_b2(s3_key)
        if encrypted_data is None or len(encrypted_data) == 0:
            return jsonify({'error': 'Failed to download file from storage or file is empty'}), 500
            
        # Step 7: Decrypt the file
        cipher = Cipher(algorithms.AES(file_aes_key), modes.CBC(file_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # Safety check to prevent index error
        if len(padded_data) == 0:
            return jsonify({'error': 'Decryption resulted in empty data'}), 400
            
        # Handle padding for file data
        pad_len = padded_data[-1]
        if not (1 <= pad_len <= 16):
            print(f"Invalid file padding value: {pad_len}")
            return jsonify({'error': 'Corrupted file data or invalid padding'}), 400
            
        # Make sure we don't go out of bounds
        if pad_len <= len(padded_data):
            decrypted_data = padded_data[:-pad_len]
        else:
            # Something is wrong with the padding
            return jsonify({'error': 'Invalid padding value exceeds data length'}), 400
        
        # Step 8: Send the file
        response = send_file(
            BytesIO(decrypted_data),
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type
        )
        
        # Add CORS headers to the response
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full stack trace to console
        print(f"Unexpected error in download_file: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/download_raw/<file_id>', methods=['POST', 'OPTIONS'])
def download_raw_file(file_id):
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing or invalid JSON data'}), 400
        
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Step 1: Get user info
        cursor.execute("SELECT id, aes_salt FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_id = user['id']
        
        
        # Step 3: Check file permission for this user
        cursor.execute(
            "SELECT 1 FROM file_permissions WHERE file_id = %s AND user_id = %s", 
            (file_id, user_id)
        )
        if cursor.fetchone() is None:
            return jsonify({'error': 'No access to this file'}), 403
        
        # Step 4: Fetch file metadata (filename, mime_type)
        cursor.execute("SELECT s3_key, filename, mime_type FROM files WHERE id = %s", (file_id,))
        file_meta = cursor.fetchone()
        if not file_meta:
            return jsonify({'error': 'File not found'}), 404
        
        s3_key = file_meta['s3_key']
        filename = file_meta['filename']
        mime_type = file_meta['mime_type']
        
        # Step 5: Download raw encrypted file from B2
        encrypted_data = download_file_from_b2(s3_key)
        if encrypted_data is None or len(encrypted_data) == 0:
            return jsonify({'error': 'Failed to download file from storage or file is empty'}), 500
        
        # Step 6: Send raw encrypted file data directly without decrypting
        response = send_file(
            BytesIO(encrypted_data),
            as_attachment=True,
            download_name=filename,
            mimetype=mime_type
        )
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/debug-key', methods=['POST'])
def debug_private_key():
    """
    Debug endpoint to verify key decryption without file access.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
        
    # Get user info
    cursor.execute("SELECT id, encrypted_private_key, aes_salt, aes_iv FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    encrypted_private_key = b64decode(user['encrypted_private_key'])
    salt = b64decode(user['aes_salt'])
    iv = b64decode(user['aes_iv'])
    
    # Stats for debugging
    stats = {
        'encrypted_key_length': len(encrypted_private_key),
        'salt_length': len(salt),
        'iv_length': len(iv),
        'password_length': len(password)
    }
    
    # Derive AES key
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000, backend=default_backend())
    aes_key = kdf.derive(password.encode())
    
    # Try decryption
    cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_private_key) + decryptor.finalize()
    
    # Check for PEM format
    stats['begins_with_pem'] = decrypted_data.startswith(b'-----BEGIN')
    
    # First 50 bytes for inspection (as hex)
    stats['first_50_bytes_hex'] = decrypted_data[:50].hex()
    
    # Sample of the binary data
    stats['sample_decrypted'] = b64encode(decrypted_data[:100]).decode()
    
    # Try to load key
    key_load_result = "Failed"
    try:
        private_key = serialization.load_pem_private_key(
            decrypted_data, 
            password=None, 
            backend=default_backend()
        )
        key_load_result = "Success"
    except Exception as e:
        key_load_result = f"Error: {str(e)}"
    
    stats['key_load_result'] = key_load_result
    
    return jsonify({
        'message': 'Key debugging information',
        'stats': stats
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
