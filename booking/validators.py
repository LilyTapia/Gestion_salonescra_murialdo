from django.core.exceptions import ValidationError


def validate_institutional_email(email: str, domain: str = "murialdovalpo.cl"):
    if not email.lower().endswith("@" + domain.lower()):
        raise ValidationError(f"Debes usar tu correo institucional *@{domain}*.")
