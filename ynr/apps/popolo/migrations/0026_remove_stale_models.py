# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-16 11:27
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("popolo", "0025_move_person_fk_to_people_app"),
        ("uk_results", "0047_auto_20180501_1359"),
        ("results", "0026_move_person_fk_to_people_app"),
    ]

    operations = [
        migrations.RemoveField(model_name="link", name="content_type"),
        migrations.RemoveField(model_name="person", name="not_standing"),
        migrations.DeleteModel(name="Link"),
        migrations.DeleteModel(name="Person"),
    ]
