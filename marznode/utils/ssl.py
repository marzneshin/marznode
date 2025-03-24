"""utilities for ssl key generation and context creation"""

import ssl

from OpenSSL import crypto


def generate_random_certificate() -> tuple:
    """
    generate a random certificate
    :return:
    """
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)
    cert = crypto.X509()
    # cert.get_subject().CN = "Marzneshin"
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, "sha512")
    cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8")
    key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8")

    return key_pem, cert_pem


def generate_keypair(key_path: str, cert_path: str) -> None:
    """
    generate a keypair and write it to files
    :param key_path:
    :param cert_path:
    :return: nothing
    """
    key, cert = generate_random_certificate()

    with open(key_path, "w", encoding="utf-8") as file:
        file.write(key)

    with open(cert_path, "w", encoding="utf-8") as file:
        file.write(cert)


def create_secure_context(
    server_cert: str, server_key: str, *, trusted: str
) -> ssl.SSLContext:
    """
    creates a context in which the client is verified by the certificate specified as trusted
    :param server_cert: path to server certificate
    :param server_key: path to server private key
    :param trusted: path to client certificate
    :return: a ssl context
    """
    ctx = ssl.create_default_context(
        ssl.Purpose.CLIENT_AUTH,
        cafile=trusted,
    )
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.load_cert_chain(server_cert, server_key)
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(["h2"])
    return ctx
