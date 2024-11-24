"""Used to generate uuid/password based on the seed"""

import uuid

import xxhash

from marznode.config import AuthAlgorithm, AUTH_GENERATION_ALGORITHM


def generate_uuid(key: str) -> uuid.UUID:
    """
    generates a uuid based on key as seed
    :param key: seed used to generate the uuid
    :return: the uuid
    """
    if AUTH_GENERATION_ALGORITHM == AuthAlgorithm.PLAIN:
        return uuid.UUID(key)
    else:
        return uuid.UUID(bytes=xxhash.xxh128(key.encode()).digest())


def generate_password(key: str) -> str:
    """
    generates a hex string based on the key as seed
    :param key: the seed
    :return: a 32 characters long hex string
    """
    if AUTH_GENERATION_ALGORITHM == AuthAlgorithm.PLAIN:
        return key
    else:
        return xxhash.xxh128(key.encode()).hexdigest()
