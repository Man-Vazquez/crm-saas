import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    """
    Deriva una clave Fernet de 32 bytes a partir del SECRET_KEY existente.
    Fernet requiere exactamente 32 bytes en base64url.
    """
    key = settings.SECRET_KEY.encode()[:32].ljust(32, b"=")
    b64_key = base64.urlsafe_b64encode(key)
    return Fernet(b64_key)


def encrypt_config(config: dict) -> dict:
    """
    Encripta los valores sensibles de un config dict.
    Solo encripta campos que terminan en _password, _token, _secret.
    El resto se guarda en texto plano (host, port, user, etc.)
    """
    f = _get_fernet()
    encrypted = {}
    sensitive_suffixes = ("_password", "_token", "_secret")

    for key, value in config.items():
        if isinstance(value, str) and key.endswith(sensitive_suffixes):
            encrypted_bytes = f.encrypt(value.encode())
            encrypted[key] = f"enc:{encrypted_bytes.decode()}"
        else:
            encrypted[key] = value

    return encrypted


def decrypt_config(config: dict) -> dict:
    """
    Desencripta los valores sensibles de un config dict.
    Solo desencripta valores que empiezan con el prefijo 'enc:'.
    """
    f = _get_fernet()
    decrypted = {}

    for key, value in config.items():
        if isinstance(value, str) and value.startswith("enc:"):
            encrypted_bytes = value[4:].encode()
            decrypted[key] = f.decrypt(encrypted_bytes).decode()
        else:
            decrypted[key] = value

    return decrypted