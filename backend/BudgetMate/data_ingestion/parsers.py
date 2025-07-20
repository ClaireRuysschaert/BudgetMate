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
from data_ingestion.models import AccountStatement, BankAccount, StatementLine
from data_ingestion.utils import get_is_shared_for_user


def parse_csv_and_create_statements(
    csv_name: str,
    date_from: datetime,
    date_to: datetime,
    statement_type: str,
    bank_account_id: int,
    user_id: int,
) -> None:
    from data_ingestion.views import map_label_to_category_and_subcategory

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
