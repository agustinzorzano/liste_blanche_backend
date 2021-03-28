"""
Copyright 2021 Venceslas Roullier, Daniel Santos Bustos, Guillem Sanyas, Julien Tagnani, Agustin Zorzano

This file is part of OpenEmailAntispam.

    OpenEmailAntispam is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    OpenEmailAntispam is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with OpenEmailAntispam.  If not, see https://www.gnu.org/licenses/.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from spam.exceptions import EncryptionError
import os
import base64
import binascii


ENCRYPTOR_PUBLIC_KEY_PATH = os.environ.get("ENCRYPTOR_PUBLIC_KEY_PATH")
ENCRYPTOR_PRIVATE_KEY_PATH = os.environ.get("ENCRYPTOR_PRIVATE_KEY_PATH")


def get_key(path, key_type, password=None):
    """It reads and returns the correct RSA key (public or private)"""
    function = {
        "public": lambda file, pwd: serialization.load_pem_public_key(file.read(), backend=default_backend()),
        "private": lambda file, pwd: serialization.load_pem_private_key(
            file.read(), password=pwd, backend=default_backend()
        ),
    }
    with open(path, "rb") as key_file:
        key = function[key_type](key_file, password)
    return key


class Encryptor:
    @staticmethod
    def encrypt(raw_text):
        """It encrypts the message using RSA"""
        try:
            public_key = get_key(ENCRYPTOR_PUBLIC_KEY_PATH, "public")
            encrypted = public_key.encrypt(
                raw_text.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return base64.urlsafe_b64encode(encrypted).decode()
        except (binascii.Error, ValueError):
            raise EncryptionError

    @staticmethod
    def decrypt(cipher_text):
        """It decrypts the message using RSA"""
        private_key = get_key(ENCRYPTOR_PRIVATE_KEY_PATH, "private")

        try:
            original_message = private_key.decrypt(
                base64.urlsafe_b64decode(cipher_text.encode()),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        except (binascii.Error, ValueError):
            raise EncryptionError
        return original_message.decode()
