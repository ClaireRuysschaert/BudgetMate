# Generated by Django 4.1.13 on 2025-07-14 13:49

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("data_ingestion", "0008_alter_sharerule_always_shared_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="statementline",
            name="operation_type",
            field=models.CharField(
                choices=[
                    ("DD", "Direct Debit"),
                    ("CB", "Bank Card"),
                    ("CH", "Cheque"),
                    ("CA", "Cash"),
                    ("RE", "Refund"),
                    ("IN", "Interest"),
                    ("TR", "Transfer"),
                    ("BF", "Bank Fees"),
                    ("OT", "Other"),
                ],
                max_length=255,
            ),
        ),
        migrations.CreateModel(
            name="LabelCategoryMapping",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(max_length=200)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_ingestion.category",
                    ),
                ),
                (
                    "sub_category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="data_ingestion.subcategory",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "label")},
            },
        ),
    ]
