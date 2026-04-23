from hashids import Hashids
from django.conf import settings

salt = getattr(settings, 'HASHIDS_SALT', settings.SECRET_KEY)
hash_tool = Hashids(salt=salt, min_length=8)

def encode_ref(number):
    return hash_tool.encode(number)

def decode_ref(hashed_text):
    decoded = hash_tool.decode(hashed_text)
    return decoded[0] if decoded else None