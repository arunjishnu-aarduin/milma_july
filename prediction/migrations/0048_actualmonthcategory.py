# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-31 07:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0047_auto_20171030_1538'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActualMonthCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField()),
                ('month', models.PositiveSmallIntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')])),
                ('actual_sale', models.PositiveIntegerField()),
                ('actual_stockin', models.PositiveIntegerField()),
                ('actual_stockout', models.PositiveIntegerField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Category')),
                ('diary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary')),
            ],
        ),
    ]
