from typing import List, Callable
import re
from decimal import Decimal
from collections import defaultdict
from bs4.dammit import UnicodeDammit
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
from datetime import datetime
from data_ingestion.models import StatementLine, Category, SubCategory, AccountStatement, BankAccount, ShareRule, LabelCategoryMapping
from accounts.models import User
from data_ingestion.utils import get_is_shared_for_user
from data_ingestion.constants import OPERATION_TYPE_MAP

"""
Different banks will have different ways of formatting data.
This file contains class that will contain the different regex
used by each bank to format Statement Lines so we can parse
them and create lines accordingly.
"""

class LabelPattern:
    """
    Define and apply regex patterns to extract information from labels
    """
    def __init__(self, start_token=r'', end_token=r''):
        self.start_token = start_token
        self.end_token = end_token

    @property
    def pattern(self):
        return re.compile(self.start_token + r"(.*)" + self.end_token)

    def extract_content(self, label: str) -> str | None:
        """Extract string located between start_token and end_token if any"""
        search_result = self.pattern.search(label)
        if search_result:
            # " ".join() is used to remove any extra space between words
            return " ".join(search_result.group(2).split())
        else:
            return None


class StatementParser:
    """
    Parser class to extract source or destination from a StatementLine's label.
    """
    def parse_label(self, label: str) -> str | None:
        """Extract information from a StatementLine's label (source or destination)."""
        regex_methods: List[Callable] = [getattr(self, func_name) for func_name in self.get_label_regex_methods()]
        for method in regex_methods:
            try:
                # If the function is present but not implemented, ignore it
                label_pattern: LabelPattern = method()
            except NotImplementedError:
                continue

            content = label_pattern.extract_content(label)
            if content:
                return content

    def get_label_regex_methods(self) -> list:
        """Get all functions with get_..._label_regex in their name."""
        regex_in_name = re.compile(r"get_.*_label_regex")
        method_list  = [
            func
            for func in dir(self)
            if callable(getattr(self, func))
            # No need for dunder methods
            and not func.startswith("__")
        ]
        results = list(filter(regex_in_name.search, method_list))
        return results

    def achat_label_pattern(self):
        raise NotImplementedError("Parser subclasses must define get_achat_label_regex")
    
    def virement_label_pattern(self):
        raise NotImplementedError("Parser subclasses must define get_virement_label_regex")

    def prelevement_label_pattern(self):
        raise NotImplementedError("Parser subclasses must define get_prelevement_label_regex")

class LaBanquePostaleParser(StatementParser):
    def achat_label_pattern(self):
        return LabelPattern(
                start_token=r"(ACHAT\sCB)\s*",
                end_token=r"\s(\d{2}\.\d{2}\.\d{2})"
        )

    def prelevement_label_pattern(self):
        return LabelPattern(
            start_token=r'(PRELEVEMENT\sDE)\s',
            end_token=r'\s(REF\s\:)'
        )

    def virement_label_pattern(self):
        return LabelPattern(
            start_token=r'(VIREMENT\sDE)\s',
            end_token=r'\s(REFERENCE\s\:)'
        )

class CaisseDepargneParser(StatementParser):
        def achat_label_pattern(self):
            LabelPattern(
                start_token=r"CB",
            )
        
        def virement_label_pattern(self):
            LabelPattern(
                start_token=r"PRLV",
            )
        
        def prelevement_label_pattern(self):
            LabelPattern(
                start_token=r"PRLV",
            )

import unicodedata

def clean_string(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")

def prompt_for_category(label: str, category_name: str, sub_category_name: str) -> tuple[str | None, str | None]:
    print(f"\nNew label detected: {label}")
    # Category input loop
    while True:
        cat_input = input(f"Proposed category: '{category_name}'. Type 'yes' to accept, or enter a new category (or 'q' to quit): ").strip()
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
        subcat_input = input(f"Proposed sub-category: '{sub_category_name}'. Type 'yes' to accept, or enter a new sub-category (or 'q' to quit): ").strip()
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

def parse_csv_and_create_statements(csv_name: str, date_from: datetime , date_to: datetime, statement_type: str, bank_account_id: int, user_id: int) -> None:
    user = User.objects.get(id=user_id)
    account_statement, created = AccountStatement.objects.get_or_create(
        start_date=date_from,
        end_date=date_to,
        statement_type=statement_type,
        bank_account=BankAccount.objects.get(id=bank_account_id, user=user)
        )
    if not created and account_statement.statementline_set.exists():
        print(f"Account statement for {date_from} to {date_to} already exists.")
        return
    csv_path = Path(__file__).parent / "fixtures" / csv_name
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        csv_reader = csv.reader(f, delimiter=';')
        header = next(csv_reader)
        for row in csv_reader:
            label = row[1]
            comment = row[2]
            operation_type_raw = row[5]
            category_name_csv = row[6]
            sub_category_name_csv = row[7]
            debit_amount = row[8]
            credit_amount = row[9]
            operation_date = row[10]

            operation_type = OPERATION_TYPE_MAP.get(operation_type_raw, "OT")

            mapping = LabelCategoryMapping.objects.filter(user=user, label=label).first()
            if mapping:
                category = mapping.category
                sub_category = mapping.sub_category
            else:
                cat_name, subcat_name = prompt_for_category(label, category_name_csv, sub_category_name_csv)
                if cat_name:
                    cat_name = clean_string(cat_name)
                if subcat_name:
                    subcat_name = clean_string(subcat_name)
                category = Category.objects.get_or_create(name=cat_name, user=user)[0] if cat_name else None
                sub_category = None
                if subcat_name and category:
                    sub_category = SubCategory.objects.get_or_create(name=subcat_name, category=category, user=user)[0]
                if category and sub_category:
                    LabelCategoryMapping.objects.create(user=user, label=label, category=category, sub_category=sub_category)
            
            amount = None
            if debit_amount:
                amount = Decimal(float(debit_amount.replace(',', '.')))
            elif credit_amount:
                amount = Decimal(float(credit_amount.replace(',', '.')))

            is_shared = get_is_shared_for_user(user, label, sub_category) if sub_category else None
            
            StatementLine.objects.get_or_create(
                account_statement=account_statement,
                libeller=label,
                comment=comment,
                operation_type=operation_type,
                category=category,
                sub_category=sub_category,
                amount=amount,
                operation_date=datetime.strptime(operation_date, "%d/%m/%Y").date() if operation_date else None,
                is_shared=is_shared
            )

def ask_shared_decision(statement_line: StatementLine, user: User) -> None:
    print(f"\n Line : {statement_line.libeller} | {statement_line.amount} | {statement_line.operation_date} | Category: {statement_line.category} | Subcategory: {statement_line.sub_category}")
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
            defaults={"always_shared": True}
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
            defaults={"always_shared": False}
        )
        statement_line.is_shared = False
        statement_line.save()
    else:
        print("Invalid choice, line ignored.")

def cli_set_shared_for_unclassified(user_id: int, statement_type:str) -> None:
    user = User.objects.get(id=user_id)
    account_statement = AccountStatement.objects.filter(bank_account__user__id=user_id, statement_type=statement_type).last()
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
    user_id: int
) -> None:
    """
    Parse multiple CSV files and prompt the user to set sharing rules for unclassified lines.
    Prints total shared amounts for each account statement and by category.
    csv_file :  [("file1.csv", "type1"), ("file2.csv", "type2")]
    """
    imported_statements = []
    for csv_name, statement_type in csv_files:
        print(f"\n--- Importing {csv_name} ---")
        parse_csv_and_create_statements(
            csv_name, date_from, date_to, statement_type, bank_account_id, user_id
        )
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
