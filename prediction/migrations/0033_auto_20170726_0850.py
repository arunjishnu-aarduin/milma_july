# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-26 08:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0032_auto_20170726_0841'),
    ]

    operations = [
        migrations.RenameField(
            model_name='configurationattribute',
            old_name='composition_status',
            new_name='issue_requirement_change_status',
        ),
    ]
