from typing import List, Callable
import re
from decimal import Decimal
from collections import defaultdict
from bs4.dammit import UnicodeDammit
from dataclasses import dataclass
from datetime import datetime

"""
Different banks will have different ways of formatting data.
This file contains class that will contain the different regex
used by each bank to format Statement Lines so we can parse
them and create lines accordingly.
"""

class LabelRegex:

        def __init__(self, start_token=r'', end_token=r''):
            self.start_token = start_token
            self.end_token = end_token

        @property
        def full_regex(self):
            return re.compile(self.start_token + r"(.*)" + self.end_token)

        def get_source_or_destination(self, label: str) -> str | None:
            """Extract string located between start_token and end_token if any"""
            search_result = self.full_regex.search(label)
            if search_result:
                # " ".join() is used to remove any extra space between words
                return " ".join(search_result.group(2).split())
            else:
                return None


class Parser:

    def get_source_or_destination(self, label: str) -> str | None:
        """Extract source or destination of a StatementLine's label."""
        regex_methods: List[Callable] = [getattr(self, func_name) for func_name in self.get_regex_functions()]
        for method in regex_methods:
            try:
                # If the function is present but not implemented, ignore it
                label_parser: LabelRegex = method()
            except NotImplementedError:
                continue

            source_or_destination = label_parser.get_source_or_destination(label)
            if source_or_destination:
                return source_or_destination

    def get_regex_functions(self) -> list:
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

    def get_achat_label_regex(self):
        raise NotImplementedError("Parser subclasses must define get_achat_label_regex")
    
    def get_virement_label_regex(self):
        raise NotImplementedError("Parser subclasses must define get_virement_label_regex")

    def get_prelevement_label_regex(self):
        raise NotImplementedError("Parser subclasses must define get_prelevement_label_regex")

class LaBanquePostaleParser(Parser):
    
    def get_achat_label_regex(self):
        return LabelRegex(
                start_token=r"(ACHAT\sCB)\s*",
                end_token=r"\s(\d{2}\.\d{2}\.\d{2})"
        )

    def get_virement_label_regex(self):
        return LabelRegex(
            start_token=r'(PRELEVEMENT\sDE)\s',
            end_token=r'\s(REF\s\:)'
        )

    def get_prelevement_label_regex(self):
        return LabelRegex(
            start_token=r'(VIREMENT\sDE)\s',
            end_token=r'\s(REFERENCE\s\:)'
        )
