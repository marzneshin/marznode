"""Used to generate uuid/password based on the seed"""

import uuid

import xxhash


def generate_uuid(key: str) -> uuid.UUID:
    """
    generates a uuid based on key as seed
    :param key: seed used to generate the uuid
    :return: the uuid
    """
    return uuid.UUID(bytes=xxhash.xxh128(key.encode()).digest())


def generate_password(key: str) -> str:
    """
    generates a hex string based on the key as seed
    :param key: the seed
    :return: a 32 characters long hex string
    """
    return xxhash.xxh128(key.encode()).hexdigest()

def generate_uuid_v2(key: str) -> str:
    """
    generates a reversible UUID-like string based on key as seed
    :param key: the seed
    :return: the uuid
    """
    return str(uuid.UUID(key))

def generate_password_v2(key: str) -> str:
    """
    generates a reversible password based on the key as seed
    :param key: the seed
    :return: the key
    """
    return key
