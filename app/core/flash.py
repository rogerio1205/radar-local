from fastapi import Request

FLASH_KEY = "_flash"

def flash(request: Request, message: str, category: str = "info") -> None:
    bucket = request.session.get(FLASH_KEY, [])
    if not isinstance(bucket, list):
        bucket = []
    bucket.append({"message": message, "category": category})
    request.session[FLASH_KEY] = bucket

def pop_flashes(request: Request):
    bucket = request.session.get(FLASH_KEY, [])
    request.session[FLASH_KEY] = []
    return bucket