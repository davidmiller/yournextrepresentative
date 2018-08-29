# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-21 20:34
from __future__ import unicode_literals

from django.db import migrations


def add_extra_fields_to_base(apps, schema_editor):
    PostExtraElection = apps.get_model("candidates", "PostExtraElection")

    for pee in PostExtraElection.objects.all().select_related(
        "postextra__base"
    ):
        pee.post = pee.postextra.base
        pee.save()


class Migration(migrations.Migration):

    dependencies = [("candidates", "0047_add_post_to_pee")]

    operations = [
        migrations.RunPython(
            add_extra_fields_to_base, migrations.RunPython.noop
        )
    ]
