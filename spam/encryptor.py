from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import os
import base64
import binascii


ENCRYPTOR_PUBLIC_KEY_PATH = os.environ.get("ENCRYPTOR_PUBLIC_KEY_PATH")
ENCRYPTOR_PRIVATE_KEY_PATH = os.environ.get("ENCRYPTOR_PRIVATE_KEY_PATH")


def get_key(path, key_type, password=None):
    function = {
        'public': lambda file, pwd: serialization.load_pem_public_key(file.read(), backend=default_backend()),
        'private': lambda file, pwd: serialization.load_pem_private_key(file.read(), password=pwd, backend=default_backend())
    }
    with open(path, "rb") as key_file:
        key = function[key_type](key_file, password)
    return key


class Encryptor:
    @staticmethod
    def encrypt(raw_text):
        public_key = get_key(ENCRYPTOR_PUBLIC_KEY_PATH, 'public')
        encrypted = public_key.encrypt(
            raw_text.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.urlsafe_b64encode(encrypted).decode()

    @staticmethod
    def decrypt(cipher_text):
        private_key = get_key(ENCRYPTOR_PRIVATE_KEY_PATH, 'private')

        try:
            original_message = private_key.decrypt(
                base64.urlsafe_b64decode(cipher_text.encode()),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except (binascii.Error, ValueError):
            raise IOError  # EncryptionError
        return original_message.decode()
