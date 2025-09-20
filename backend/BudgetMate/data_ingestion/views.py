from datetime import datetime

from rest_framework import generics
from rest_framework.response import Response

from accounts.models import User
from data_ingestion.models import (
    AccountStatement,
    Category,
    LabelCategoryMapping,
    ShareRule,
    StatementLine,
    SubCategory,
)
from data_ingestion.parsers import parse_csv_and_create_statements
from data_ingestion.utils import clean_string


class UploadFileView(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        # Show content of csv file
        print(request.data["file"].read().decode("utf-8"))
        return Response({"message": "POST: Received a file!"})


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

    # Look for existing category first, create if not found
    try:
        category = Category.objects.get(name=cat_name, user=user)
        print(f"Found existing category: {cat_name}")
    except Category.DoesNotExist:
        category = Category.objects.create(name=cat_name, user=user)
        print(f"Created new category: {cat_name}")

    sub_category = None
    if subcat_name and category:
        # Look for existing subcategory first, create if not found
        try:
            sub_category = SubCategory.objects.get(name=subcat_name, category=category, user=user)
            print(f"Found existing subcategory: {subcat_name}")
        except SubCategory.DoesNotExist:
            sub_category = SubCategory.objects.create(name=subcat_name, category=category, user=user)
            print(f"Created new subcategory: {subcat_name}")

    # Create the mapping for future use
    if category and sub_category:
        LabelCategoryMapping.objects.create(
            user=user,
            label=label,
            category=category,
            sub_category=sub_category,
        )

    return category, sub_category


def prompt_for_category(label: str, category_name: str, sub_category_name: str) -> tuple[str | None, str | None]:
    print(f"\nNew label detected: {label}")
    # Category input loop
    while True:
        cat_input = input(
            f"Proposed category: '{category_name}'. Type 'yes' to accept, or enter a new category (or 'q' to quit): "
        ).strip()
        if cat_input.lower() == "q":
            print("Input cancelled.")
            return None, None
        if cat_input.lower() in ["yes", "", "y"]:
            category = category_name
        else:
            category = cat_input if cat_input else category_name
        if category:
            break
        print("Please enter a category or quit.")

    # Sub-category input loop
    while True:
        subcat_input = input(
            f"Proposed sub-category: '{sub_category_name}'. Type 'yes' to accept, or enter a new sub-category (or 'q' to quit): "
        ).strip()
        if subcat_input.lower() == "q":
            print("Input cancelled.")
            return None, None
        if subcat_input.lower() in ["yes", "", "y"]:
            sub_category = sub_category_name
        else:
            sub_category = subcat_input if subcat_input else sub_category_name
        if sub_category:
            break
        print("Please enter a sub-category or quit.")

    return category.strip(), sub_category.strip()


def ask_shared_decision(statement_line: StatementLine, user: User) -> None:
    print(
        f"\n Line : {statement_line.libeller} | {statement_line.amount} | {statement_line.operation_date} | Category: {statement_line.category} | Subcategory: {statement_line.sub_category}"
    )

    # Check if we need to prompt for a new subcategory
    if (
        statement_line.category
        and statement_line.category.name.lower() == "shopping"
        and statement_line.sub_category
        and statement_line.sub_category.name == "Shopping et services - autre"
    ):
        print("\nThis transaction is categorized as 'Shopping et services - autre'.")
        print("Would you like to specify a more precise subcategory?")
        print("1 - Keep current subcategory")
        print("2 - Create a new subcategory")
        print("3 - Change both category and subcategory")

        choice = input("Your choice (1/2/3): ").strip()

        if choice == "2":
            new_subcat_name = input("Enter the new subcategory name: ").strip()
            if new_subcat_name:
                new_subcat_clean_name = clean_string(new_subcat_name)
                new_sub_category, _ = SubCategory.objects.get_or_create(
                    name=new_subcat_clean_name, user=user, category=statement_line.category
                )
                statement_line.sub_category = new_sub_category
                statement_line.save()
                print(f"New subcategory created and assigned: {new_subcat_clean_name}.\n")
            else:
                print("No subcategory name provided, keeping current one.")
        elif choice == "3":
            new_cat_name = input("Enter the new category name: ").strip()
            if new_cat_name:
                new_cat_clean_name = clean_string(new_cat_name)
                new_category, _ = Category.objects.get_or_create(name=new_cat_clean_name, user=user)
                new_subcat_name = input("Enter the new subcategory name: ").strip()
                if new_subcat_name:
                    new_subcat_clean_name = clean_string(new_subcat_name)
                    new_sub_category, _ = SubCategory.objects.get_or_create(
                        name=new_subcat_clean_name, user=user, category=new_category
                    )
                    statement_line.category = new_category
                    statement_line.sub_category = new_sub_category
                    statement_line.save()

                    print(f"New category created: {new_cat_clean_name}\n")
                    print(f"New subcategory created: {new_subcat_clean_name}\n")
            else:
                print("No subcategory name provided, keeping current categorization.")
        elif choice != "1":
            print("Invalid choice, keeping current subcategory.")

    print("\nShare this line ?")
    print("1 - Yes, but only for this statement")
    print("2 - Yes forever (create a share rule)")
    print("3 - No, but only for this statement")
    print("4 - No, Never (create a share rule)")
    choice = input("Your choice : (1/2/3/4) : ").strip()
    if choice == "1":
        statement_line.is_shared = True
        statement_line.save()
    elif choice == "2":
        ShareRule.objects.get_or_create(
            user=user,
            label=statement_line.libeller,
            sub_category=statement_line.sub_category,
            defaults={"always_shared": True},
        )
        statement_line.is_shared = True
        statement_line.save()
    elif choice == "3":
        statement_line.is_shared = False
        statement_line.save()
    elif choice == "4":
        ShareRule.objects.get_or_create(
            user=user,
            label=statement_line.libeller,
            sub_category=statement_line.sub_category,
            defaults={"always_shared": False},
        )
        statement_line.is_shared = False
        statement_line.save()
    else:
        print("Invalid choice, line ignored.")
        # TODO : do a while loop until valid input


def cli_set_shared_for_unclassified(user_id: int, statement_type: str) -> None:
    user = User.objects.get(id=user_id)
    account_statement = AccountStatement.objects.filter(
        bank_account__user__id=user_id, statement_type=statement_type
    ).last()
    lines = StatementLine.objects.filter(is_shared__isnull=True, account_statement=account_statement)
    for line in lines:
        ask_shared_decision(line, user)
    print("Done! All unclassified lines have been processed.")
    account_statement.total_shared_amount_by_category()
    print(account_statement.total_shared_amount())


def import_and_set_shared_for_files(
    csv_files: list[tuple[str, str]],
    date_from: datetime,
    date_to: datetime,
    bank_account_id: int,
    user_id: int,
) -> None:
    """
    Parse multiple CSV files and prompt the user to set sharing rules for unclassified lines.
    Prints total shared amounts for each account statement and by category.
    csv_file :  [("file1.csv", "type1"), ("file2.csv", "type2")]
    """
    imported_statements = []
    for csv_name, statement_type in csv_files:
        print(f"\n--- Importing {csv_name} ---")
        parse_csv_and_create_statements(csv_name, date_from, date_to, statement_type, bank_account_id, user_id)
        account_statement = AccountStatement.objects.filter(
            bank_account__user__id=user_id, statement_type=statement_type
        ).last()
        imported_statements.append(account_statement)
        print(f"Parsing done for {csv_name}.")

    print("\n--- Setting shared status for all imported statements ---")
    for account_statement in imported_statements:
        lines = StatementLine.objects.filter(is_shared__isnull=True, account_statement=account_statement)
        user = account_statement.bank_account.user
        for line in lines:
            ask_shared_decision(line, user)
        print(f"\nTotals for statement from {account_statement.start_date} to {account_statement.end_date}:")
        print("Total shared amount by category:")
        print(account_statement.total_shared_amount_by_category())
        print("Total shared amount:")
        print(account_statement.total_shared_amount())
        print("-----")
        print("All lines have been processed.")
        print("-----")
