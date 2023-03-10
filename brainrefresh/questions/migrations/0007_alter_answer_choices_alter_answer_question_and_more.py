# Generated by Django 4.1 on 2023-02-08 14:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("questions", "0006_answer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="answer",
            name="choices",
            field=models.ManyToManyField(
                related_name="%(class)ss", to="questions.choice"
            ),
        ),
        migrations.AlterField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to="questions.question",
            ),
        ),
        migrations.AlterField(
            model_name="answer",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)ss",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
