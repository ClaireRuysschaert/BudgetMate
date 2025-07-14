from typing import Union
from data_ingestion.models import ShareRule, SubCategory
from accounts.models import User
from typing import Optional

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
        sub_category__category=sub_category.category
    ).first()
    if rule:
        return bool(rule.always_shared)
    return None
