# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-21 08:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0022_auto_20170720_0959'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')])),
                ('requirement', models.DecimalField(decimal_places=4, max_digits=10)),
                ('diary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Issue')),
            ],
        ),
    ]
