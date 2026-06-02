import re

def normalize_name(name: str) -> str:
    """Normaliza nome."""
    if not name:
        return ""
    return name.strip().upper()

def normalize_cpf(cpf: str) -> str:
    """Normaliza CPF."""
    if not cpf:
        return ""
    return re.sub(r'[^0-9]', '', cpf)

def normalize_birth_date(birth_date: str) -> str:
    """Normaliza data nascimento."""
    if not birth_date:
        return ""
    return birth_date.strip()
