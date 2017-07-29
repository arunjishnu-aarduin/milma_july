# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-28 09:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0035_auto_20170727_0410'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterStockCreamTransferOrder',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.PositiveSmallIntegerField()),
                ('from_diary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_dairy', to='prediction.Diary', verbose_name='from dairy')),
                ('to_diary', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='interstockcreamtransferorder',
            unique_together=set([('from_diary', 'to_diary')]),
        ),
    ]