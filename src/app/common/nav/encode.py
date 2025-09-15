from hashids import Hashids
hashids = Hashids(salt="7M3a3ePnLDVvoC06W03gw3rxS9ra5vZQ", min_length=15)

def encode_id(id: int) -> str:
    return hashids.encode(id)

def decode_id(hash_id: str) -> int:
    decoded = hashids.decode(hash_id)
    return decoded[0] if decoded else None
