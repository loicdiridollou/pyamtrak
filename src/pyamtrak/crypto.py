"""Tools and methods to decode values from Amtrak endpoints."""

import base64
import json

import requests
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import unpad

MASTER_SEGMENT = 88


def get_crypto_parameters(url: str | None = None) -> tuple[str, str, str]:
    """Get parameters to create a decryption key."""
    crypto_data = requests.get(
        url or "https://maps.amtrak.com/rttl/js/RoutesList.v.json"
    ).json()

    master_zoom = sum(
        v.get("ZoomLevel", 0)
        for v in requests.get("https://maps.amtrak.com/rttl/js/RoutesList.json").json()
    )
    public_key = crypto_data["arr"][master_zoom]
    salt = crypto_data["s"][len(crypto_data["s"][0])]
    iv = crypto_data["v"][len(crypto_data["v"][0])]

    return public_key, salt, iv


def _decrypt(content: str, key: str, s_value: str, i_value: str) -> str:
    """
    Decrypt content.

    Parameters
    ----------
        content: Base64 encoded encrypted content
        key: Decryption key

    Returns
    -------
        Decrypted string
    """
    # Derive key using PBKDF2
    salt = bytes.fromhex(s_value)
    derived_key = PBKDF2(key, salt, dkLen=16, count=1000)

    # Parse IV
    iv = bytes.fromhex(i_value)

    # Decode the base64 content
    ciphertext = base64.b64decode(content)

    # Create cipher and decrypt
    cipher = AES.new(derived_key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)

    # Remove PKCS7 padding
    decrypted = unpad(decrypted, AES.block_size)

    return decrypted.decode("utf-8")


def decrypt_data(
    encrypted_data: str, public_key: str, s_value: str, i_value: str
) -> dict:
    """
    Decrypt the data and clean it up.

    Parameters
    ----------
        encrypted_data: The encrypted response from Amtrak API

    Returns
    -------
        Decrypted GeoJSON data
    """
    content_hash_length = len(encrypted_data) - MASTER_SEGMENT

    # Get the two parts
    content_hash = encrypted_data[:content_hash_length]
    private_key_hash = encrypted_data[content_hash_length:]

    # Decrypt the private key and extract it (before the pipe)
    private_key = _decrypt(
        private_key_hash, public_key, s_value=s_value, i_value=i_value
    ).split("|")[0]

    # Decrypt the actual content
    decrypted_content = _decrypt(
        content_hash, private_key, s_value=s_value, i_value=i_value
    )

    # Parse JSON and extract the GeoJSON data
    data = json.loads(decrypted_content)

    return data
