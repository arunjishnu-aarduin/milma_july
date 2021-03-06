# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-27 04:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0033_auto_20170726_0850'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueUsedAsCategoryDirectOrIndirect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Category')),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Issue')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='issueusedascategorydirectorindirect',
            unique_together=set([('issue', 'category')]),
        ),
    ]
