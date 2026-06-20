from cryptography.fernet import Fernet


def generate_encryption_key() -> bytes:
    return Fernet.generate_key()


def encrypt_value(key: bytes, value: str) -> str:
    return Fernet(key).encrypt(value.encode()).decode()


def decrypt_value(key: bytes, token: str) -> str:
    return Fernet(key).decrypt(token.encode()).decode()
