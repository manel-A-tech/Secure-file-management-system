import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# generation a key (instead of the password)


def generate_key(password: str, salt: bytes = None) -> tuple:
    if salt is None:  # to add randomness
        salt = os.urandom(16)
    # specify the key derivation function
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(
        password.encode()))  # convert to ascii
    return key, salt
# encrypting the data in the file to store it


def encrypt_file(file_data: bytes, password: str) -> tuple:
    try:
        key, salt = generate_key(password)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(file_data)
        return encrypted_data, salt
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")

# decrypting the file's data


def decrypt_file(encrypted_data: bytes, password: str, salt: bytes) -> bytes:
    try:
        key, _ = generate_key(password, salt)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")

# encoding salt for the database storage


def encode_salt(salt: bytes) -> str:
    return base64.b64encode(salt).decode('utf-8')

# decode base64 salt string from database to bytes


def decode_salt(salt_str: str) -> bytes:
    return base64.b64decode(salt_str.encode('utf-8'))
