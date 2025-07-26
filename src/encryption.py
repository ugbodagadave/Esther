import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the encryption key from environment variables
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables. Please set it to a 32-byte URL-safe base64-encoded key.")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string using the application's encryption key."""
    if not data:
        return ""
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypts a string using the application's encryption key."""
    if not encrypted_data:
        return ""
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
    return decrypted_data.decode()

if __name__ == '__main__':
    # Example usage and key generation
    # To generate a new key, run this file directly: python src/encryption.py
    # Important: Keep this key safe and private.
    key = Fernet.generate_key()
    print(f"Generated a new encryption key: {key.decode()}")
    
    # Test encryption and decryption
    test_data = "my_secret_private_key"
    print(f"\nOriginal data: {test_data}")
    
    encrypted = encrypt_data(test_data)
    print(f"Encrypted data: {encrypted}")
    
    decrypted = decrypt_data(encrypted)
    print(f"Decrypted data: {decrypted}")
    
    assert test_data == decrypted
    print("\n✅ Encryption and decryption test passed.")
