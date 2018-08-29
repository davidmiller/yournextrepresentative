# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-21 20:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("popolo", "0010_rename_not_standing_related_name"),
        ("candidates", "0046_delete_person_extra"),
        ("moderation_queue", "0022_add_detection_metadata"),
        ("official_documents", "0020_add_post_election_values"),
        ("uk_results", "0047_auto_20180501_1359"),
    ]

    operations = [
        migrations.AddField(
            model_name="postextraelection",
            name="post",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="popolo.Post",
            ),
        )
    ]
