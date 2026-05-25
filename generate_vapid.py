"""
Genera le chiavi VAPID per le notifiche push.
Esegui UNA SOLA VOLTA: python generate_vapid.py
Poi copia le chiavi nel file .env
"""
import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, PublicFormat, NoEncryption
)

private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key  = private_key.public_key()

priv_bytes = private_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())
pub_bytes  = public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)

priv_b64 = base64.urlsafe_b64encode(priv_bytes).decode().rstrip('=')
pub_b64  = base64.urlsafe_b64encode(pub_bytes).decode().rstrip('=')

print("\nAggiungi queste righe al file .env:\n")
print(f"VAPID_PUBLIC_KEY={pub_b64}")
print(f"VAPID_PRIVATE_KEY={priv_b64}")
print()
