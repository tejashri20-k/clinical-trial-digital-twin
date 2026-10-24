import hashlib


def generate_hash(data):
    data_string = str(data)

    hash_object = hashlib.sha256(data_string.encode())

    return hash_object.hexdigest()