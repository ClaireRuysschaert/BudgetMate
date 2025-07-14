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
from data_ingestion.models import StatementLine, Category, SubCategory, AccountStatement, BankAccount, ShareRule
from accounts.models import User
from data_ingestion.utils import get_is_shared_for_user
import sys

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
            

# Goal : load a csv file and parse it :
# each line corresponnd to a StatementLine objects
    # - the first line is the header
    # - the second line is the first line of data
        # - the first column is the comptabilisation date to pass
        # - the third column is the label corresponding to libeller to the StatementLine object
        # - the fourth column is the reference to pass
        # - the fifth column is the more informations to pass
        # - the sixth column is the operation type corresponding to operation_type to the StatementLine object
        # - the seventh column is the category corresponding to category to the StatementLine object
        # - the eighth column is the sub-category corresponding to sub_category to the StatementLine object
        # - the ninth column is the debit amount corresponding to amount to the StatementLine object
        # - the tenth column is the credit amount corresponding to amount to the StatementLine object
        # - the eleventh column is the date corresponding to operation_date to the StatementLine object
        # - the twelfth column is the value date to pass
        # - the thirteenth column is the pointage to pass


user_id = 1
bank_account_id = 1
# To parse the CSV file, the user has to provide : 
    # - the date from / date to that correspond to the account statement
    # - the bank account id that correspond to the account statement
    # - statement_type that correspond to the account statement

def parse_csv_and_create_statements(date_from, date_to, statement_type, bank_account_id, user_id) -> None:
    user = User.objects.get(id=user_id)
    account_statement = AccountStatement.objects.get_or_create(
        start_date=date_from,
        end_date=date_to,
        statement_type=statement_type,
        bank_account=BankAccount.objects.get(id=bank_account_id, user=user)
        )[0]
    csv_path = Path(__file__).parent / "fixtures" / "june_ca.csv"
    with open(csv_path, encoding="utf-8") as f:
        csv_reader = csv.reader(f, delimiter=';')
        header = next(csv_reader)
        for row in csv_reader:
            label = row[1]
            operation_type = row[5]
            category_name = row[6]
            sub_category_name = row[7]
            debit_amount = row[8]
            credit_amount = row[9]
            operation_date = row[10]

            category = Category.objects.get_or_create(name=category_name, user=user)[0] if category_name else None
            sub_category = None
            print(f"Category: {category}, Sub-category: {sub_category_name}")
            if sub_category_name and category:
                sub_category = SubCategory.objects.get_or_create(name=sub_category_name, category=category, user=user)[0]
            print(f"Sub-category: {sub_category}, {sub_category.id}")
            amount = None
            if debit_amount:
                amount = Decimal(float(debit_amount.replace(',', '.')))
            elif credit_amount:
                amount = Decimal(float(credit_amount.replace(',', '.')))

            is_shared = get_is_shared_for_user(user, label, sub_category) if sub_category else None
            
            StatementLine.objects.get_or_create(
                account_statement=account_statement,
                libeller=label,
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
    print("3 - No")
    choice = input("Your choice : (1/2/3) : ").strip()
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
    else:
        print("Invalid choice, line ignored.")

def cli_set_shared_for_unclassified(user_id):
    user = User.objects.get(id=user_id)
    account_statement = AccountStatement.objects.filter(bank_account__user__id=user_id, statement_type="CA").last()
    lines = StatementLine.objects.filter(is_shared__isnull=True, account_statement=account_statement)
    for line in lines:
        ask_shared_decision(line, user)
    print("Done! All unclassified lines have been processed.")
    account_statement.total_shared_amount_by_category()
    print(account_statement.total_shared_amount())

