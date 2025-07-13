from django.db import models
from accounts.models import User

class BankBrand(models.Model):
    name = models.CharField(max_length=255)
    
    # TODO: logo ImageField ?
    def __str__(self):
        return self.name


class BankAccount(models.Model):
    account_number = models.CharField(max_length=255)
    bank: BankBrand = models.ForeignKey(
        "BankBrand",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.account_number} ({self.bank.name}) _ {self.user.username}"


class StatementType(models.TextChoices):
    """
    Type of file format for the bank statement.
    """
    BANK_STATEMENT = "BS", "Bank Statement"
    RECEIPTS = "CA", "Card Receipts" #Facturettes
    CREDIT = "CR", "Credit"
    DEBIT = "DB", "Debit"
    OTHER = "OT", "Other"


class AccountStatement(models.Model):
    """
    Account statement with multiple statement line (StatementLine model)
    
    """

    statement_type = models.CharField(max_length=255, choices=StatementType.choices)
    start_date = models.DateField()
    end_date = (
        models.DateField()
    )  # TODO: Vérifier dans le formulaire que l'end_date est plus vieux que le start_date
    #TODO: Verify in the form that end_date is older than start_date
    #TODO: Add the file type (pdf, csv, xls, etc)
    #TODO: check if the file is already in the database
    bank_account: BankAccount = models.ForeignKey(
        "BankAccount",
        on_delete=models.CASCADE,
    )
    def __str__(self):
        return (
            f"{self.statement_type} from {self.start_date} to {self.end_date} "
            f": {self.bank_account.user.username} in {self.bank_account.bank.name}."
        )

    def total_amount(self):
        return self.statementline_set.aggregate(total=models.Sum('amount'))['total'] or 0


class OperationType(models.TextChoices):
    """
    Type of operation for the statement line.
    """
    DD = "DD", "Direct Debit"
    CB = "CB", "Bank Card"
    CHQ = "CH", "Cheque"
    CASH = "CA", "Cash"
    REFUND = "RE", "Refund"
    INT = "IN", "Interest"
    TRANSFER = "TR", "Transfer"
    OTHER = "OT", "Other"


class StatementLine(models.Model):
    """
    Account statement line.
    Represents a single operation in an account statement.
    e.g. a bank transfer, a direct debit, a credit card payment, etc.
    """

    account_statement = models.ForeignKey(
        "AccountStatement",
        on_delete=models.CASCADE,
    )
    operation_type = models.CharField(max_length=255, choices=OperationType.choices)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    operation_date = models.DateField()
    libeller = models.CharField(max_length=200)
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, blank=True, null=True
    )
    comment = models.CharField(max_length=250, blank=True, null=True)
    is_shared = models.BooleanField(default=False)  # For cost sharing
    
    def __str__(self):
        return (
            f"{self.libeller} - {self.operation_type} - {self.amount} "
            f"on {self.operation_date} for {self.account_statement.bank_account.user.username}"
        )


class Category(models.Model):
    """
    Category for the statement line.
    e.g. groceries, utilities, entertainment, etc. #TODO: change these examples
    """
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class SubCategory(models.Model):
    """
    Subcategory for the statement line.
    e.g. for groceries: fruits, vegetables, dairy, etc. #TODO: change these examples
    """
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Subcategories"

