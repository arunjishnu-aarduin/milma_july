# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-25 09:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0030_configurationattributes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('financial_Year', models.IntegerField(choices=[(2016, 2016), (2017, 2017), (2018, 2018), (2019, 2019), (2020, 2020), (2021, 2021)], verbose_name='year')),
            ],
        ),
        migrations.DeleteModel(
            name='ConfigurationAttributes',
        ),
    ]
