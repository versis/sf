import random
import string

def generate_random_suffix(length: int = 8) -> str:
    """Generates a random alphanumeric suffix of a given length."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length)) 