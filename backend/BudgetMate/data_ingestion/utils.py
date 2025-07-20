import unicodedata
from typing import Optional

from accounts.models import User
from data_ingestion.models import ShareRule, SubCategory


def get_is_shared_for_user(user: User, label: str, sub_category: SubCategory) -> Optional[bool]:
    """
    Check if a share rule exists for the user, label, and sub_category.
    Returns True if a rule exists, otherwise False.
    This is used to determine if a statement line should be marked as shared.
    """
    rule = ShareRule.objects.filter(
        user=user,
        label__iexact=label.strip(),
        sub_category__name__iexact=sub_category.name.strip(),
        sub_category__category=sub_category.category,
    ).first()
    if rule:
        return bool(rule.always_shared)
    return None


def clean_string(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
