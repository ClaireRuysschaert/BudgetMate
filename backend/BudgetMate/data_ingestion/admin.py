from django.contrib import admin

from .models import (
    AccountStatement,
    BankAccount,
    BankBrand,
    Category,
    LabelCategoryMapping,
    ShareRule,
    StatementLine,
    SubCategory,
)


@admin.register(BankBrand)
class BankBrandAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    model = BankAccount
    list_display = ("account_number", "bank", "user", "description")


@admin.register(AccountStatement)
class AccountStatementAdmin(admin.ModelAdmin):
    model = AccountStatement
    list_display = (
        "statement_type",
        "start_date",
        "end_date",
        "bank_account_number",
        "bank_name_acc",
        "user_account",
    )

    def bank_account_number(self, obj):
        return obj.bank_account.account_number

    def bank_name_acc(self, obj):
        return obj.bank_account.bank.name

    def user_account(self, obj):
        return obj.bank_account.user


@admin.register(StatementLine)
class StatementLineAdmin(admin.ModelAdmin):
    model = StatementLine
    list_display = (
        "account_statement",
        "operation_type",
        "amount",
        "operation_date",
        "user",
        "category",
        "sub_category",
    )

    def user(self, obj):
        return obj.account_statement.bank_account.user

    search_fields = ["account_statement__bank_account__user__username"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(LabelCategoryMapping)
class LabelCategoryMappingAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "category", "sub_category")

    def user(self, obj: LabelCategoryMapping):
        return obj.user.username

    search_fields = ["user__username", "label"]


@admin.register(ShareRule)
class ShareRuleAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "sub_category", "always_shared")

    def user(self, obj: ShareRule):
        return obj.user.username

    search_fields = ["user__username", "label", "sub_category__name"]
