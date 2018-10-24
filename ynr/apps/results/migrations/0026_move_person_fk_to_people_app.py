# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-23 19:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("results", "0025_winner_party_not_null"),
        ("people", "0004_move_person_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="resultevent",
            name="winner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="people.Person"
            ),
        )
    ]
