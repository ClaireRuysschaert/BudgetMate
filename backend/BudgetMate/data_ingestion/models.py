from django.db import models
from accounts.models import User

# Create your models here.


class BankBrand(models.Model):
    name = models.CharField(max_length=255)
    # TO DO : logo ImageField ?


class BankAccount(models.Model):
    account_number = models.CharField(max_length=255)
    bank = models.ForeignKey(
        "BankBrand",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )


class StatementType(models.TextChoices):
    RB = ("RB", "Relevé de banque")
    FACT = ("FACT", "Facturettes")


class AccountStatement(models.Model):
    """
    Account statement with multiple statement line (StatementLine model)
    """

    statement_type = models.CharField(max_length=255, choices=StatementType.choices)
    start_date = models.DateField()
    end_date = (
        models.DateField()
    )  # TO DO : Vérifier dans le formulaire que l'end_date est plus vieux que le start_date
    bank_account = models.ForeignKey(
        "BankAccount",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        f"Relevé de compte couvrant du {self.start_date} au {self.end_date}."


class OperationType(models.TextChoices):
    PVT = ("PVT", "Prélèvement")
    VIR = ("VIR", "Virement")
    CB = ("CB", "Carte bancaire")


class StatementLine(models.Model):
    """
    Account statement line
    """

    account_statement = models.ForeignKey(
        "AccountStatement",
        on_delete=models.CASCADE,
    )
    operation_type = models.CharField(max_length=255, choices=OperationType.choices)
    amount = models.IntegerField()
    operation_date = models.DateField()
    libeller = models.CharField(max_length=200)
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, blank=True, null=True
    )
    sub_category = models.ForeignKey(
        "SubCategory", on_delete=models.SET_NULL, blank=True, null=True
    )
    comment = models.CharField(max_length=250, blank=True, null=True)


class Category(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)


class SubCategory(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
