import unicodedata
from typing import Optional

from accounts.models import User
from data_ingestion.models import Category, LabelCategoryMapping, ShareRule, SubCategory
from data_ingestion.views import prompt_for_category


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


def map_label_to_category_and_subcategory(
    user: User,
    label: str,
    category_name_csv: str | None = None,
    sub_category_name_csv: str | None = None,
) -> tuple[Category | None, SubCategory | None]:
    """
    Map a label to existing categories or create new ones based on user input.

    Args:
        user: User object
        label: Transaction label to categorize
        category_name_csv: Proposed category name from CSV (optional)
        sub_category_name_csv: Proposed sub-category name from CSV (optional)

    Returns:
        Tuple of (Category, SubCategory) objects
    """
    mapping = LabelCategoryMapping.objects.filter(user=user, label=label).first()
    if mapping:
        return mapping.category, mapping.sub_category

    category_name_proposal = category_name_csv or ""
    sub_category_name_proposal = sub_category_name_csv or ""

    if not category_name_proposal:
        category_name_proposal = "Uncategorized"
        sub_category_name_proposal = "Uncategorized"

    cat_name, subcat_name = prompt_for_category(label, category_name_proposal, sub_category_name_proposal)

    if not cat_name:
        return None, None
    cat_name = clean_string(cat_name)

    if subcat_name:
        subcat_name = clean_string(subcat_name)

    category = Category.objects.get_or_create(name=cat_name, user=user)[0]
    sub_category = None

    if subcat_name and category:
        sub_category = SubCategory.objects.get_or_create(name=subcat_name, category=category, user=user)[0]

    if category and sub_category:
        LabelCategoryMapping.objects.create(
            user=user,
            label=label,
            category=category,
            sub_category=sub_category,
        )

    return category, sub_category
