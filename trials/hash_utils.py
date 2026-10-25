import hashlib


def generate_hash(data):
    data_string = str(data)

    hash_object = hashlib.sha256(data_string.encode())

    return hash_object.hexdigest()


def record_data_string(record):
    """The exact string that gets hashed for a clinical record.

    Used when a record is saved, when its hash is stored on the blockchain,
    and when its integrity is verified, so all three always agree.
    """
    return (
        f"{record.record_id}|"
        f"{record.blood_pressure}|"
        f"{record.blood_glucose:g}|"
        f"{record.treatment}"
    )


def compute_record_hash(record):
    """SHA-256 of the record's CURRENT values in the database."""
    return generate_hash(record_data_string(record))