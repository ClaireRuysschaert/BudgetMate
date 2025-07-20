import csv
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from accounts.models import User
from data_ingestion.constants import (
    OPERATION_TYPE_MAP,
    REGEX_DIRECT_DEBIT,
    REGEX_INSTANT_TRANSFER,
    REGEX_PURCHASE,
    REGEX_TRANSFER,
)
from data_ingestion.models import (
    AccountStatement,
    BankAccount,
    ShareRule,
    StatementLine,
)
from data_ingestion.utils import (
    get_is_shared_for_user,
    map_label_to_category_and_subcategory,
)


def parse_csv_and_create_statements(
    csv_name: str,
    date_from: datetime,
    date_to: datetime,
    statement_type: str,
    bank_account_id: int,
    user_id: int,
) -> None:
    user = User.objects.get(id=user_id)
    account_statement, created = AccountStatement.objects.get_or_create(
        start_date=date_from,
        end_date=date_to,
        statement_type=statement_type,
        bank_account=BankAccount.objects.get(id=bank_account_id, user=user),
    )
    if not created and account_statement.statementline_set.exists():
        print(f"Account statement for {date_from} to {date_to} already exists.")
        return
    csv_path = Path(__file__).parent / "fixtures" / csv_name
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        csv_reader = csv.reader(f, delimiter=";")
        next(csv_reader)

        if account_statement.bank_account.bank.name == "Banque postale":
            print("Parsing La Banque Postale CSV file...")
            for row in csv_reader:
                if not row or len(row) < 3:
                    continue
                try:
                    operation_date = datetime.strptime(row[0], "%d/%m/%Y").date()
                except ValueError:
                    continue  # Skip rows with invalid date format (valid lines to parse)

                purchase_match = re.search(REGEX_PURCHASE, row[1])
                direct_debit_match = re.search(REGEX_DIRECT_DEBIT, row[1])
                transfer_match = re.search(REGEX_TRANSFER, row[1])
                instant_transfer_match = re.search(REGEX_INSTANT_TRANSFER, row[1])

                # Extract purchase date if it's a card purchase
                if purchase_match:
                    operation_date_raw = " ".join(purchase_match.group(3).split())
                    operation_date = datetime.strptime(operation_date_raw, "%d.%m.%y").date()

                transaction_match = purchase_match or direct_debit_match or transfer_match or instant_transfer_match
                expense_match = purchase_match or direct_debit_match
                income_match = transfer_match or instant_transfer_match

                # Extract clean label from the matched pattern
                if expense_match:
                    clean_label = " ".join(expense_match.group(2).split())
                elif income_match:
                    clean_label = " ".join(income_match.group(1 if instant_transfer_match else 2).split())
                    if "SALAIRE" in clean_label:
                        continue  # Skip salary entries

                amount = Decimal(row[2].replace(",", ".")) if row[2] else None
                operation_type_raw = " ".join(transaction_match.group(1).split()) if transaction_match else "OT"
                operation_type = OPERATION_TYPE_MAP.get(operation_type_raw, "OT")

                category, sub_category = map_label_to_category_and_subcategory(user, clean_label)

                is_shared = get_is_shared_for_user(user, clean_label, sub_category) if sub_category else None

                StatementLine.objects.get_or_create(
                    account_statement=account_statement,
                    libeller=clean_label,
                    operation_type=operation_type,
                    category=category,
                    sub_category=sub_category,
                    amount=amount,
                    operation_date=operation_date,
                    is_shared=is_shared,
                )

        elif account_statement.bank_account.bank.name == "Caisse d'épargne":
            print("Parsing Caisse d'Épargne CSV file...")
            for row in csv_reader:
                label = row[1]
                comment = row[2]
                operation_type_raw = row[5]
                category_name_csv = row[6]
                sub_category_name_csv = row[7]
                debit_amount = row[8]
                credit_amount = row[9]
                operation_date_str = row[10]

                operation_date = datetime.strptime(operation_date_str, "%d/%m/%Y").date()
                operation_type = OPERATION_TYPE_MAP.get(operation_type_raw, "OT")

                amount = None
                if debit_amount:
                    amount = Decimal(float(debit_amount.replace(",", ".")))
                elif credit_amount:
                    amount = Decimal(float(credit_amount.replace(",", ".")))

                category, sub_category = map_label_to_category_and_subcategory(
                    user, label, category_name_csv, sub_category_name_csv
                )

                is_shared = get_is_shared_for_user(user, label, sub_category) if sub_category else None

                StatementLine.objects.get_or_create(
                    account_statement=account_statement,
                    libeller=label,
                    comment=comment,
                    operation_type=operation_type,
                    category=category,
                    sub_category=sub_category,
                    amount=amount,
                    operation_date=operation_date,
                    is_shared=is_shared,
                )


def ask_shared_decision(statement_line: StatementLine, user: User) -> None:
    print(
        f"\n Line : {statement_line.libeller} | {statement_line.amount} | {statement_line.operation_date} | Category: {statement_line.category} | Subcategory: {statement_line.sub_category}"
    )
    print("Share this line ?")
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
