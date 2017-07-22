# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-22 08:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0026_auto_20170722_0840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actualstockin',
            name='from_diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fromDiary', to='prediction.Diary', verbose_name='from dairy'),
        ),
        migrations.AlterField(
            model_name='actualwmprocurement',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='interstockmilktransferorder',
            name='from_diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_Diary', to='prediction.Diary', verbose_name='from dairy'),
        ),
        migrations.AlterField(
            model_name='interstockmilktransferorder',
            name='to_diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='issuerequirement',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='procurementgrowthfactor',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='productcategorygrowthfactor',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='productconfiguration',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
        migrations.AlterField(
            model_name='userdiarylink',
            name='diary',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prediction.Diary', verbose_name='dairy'),
        ),
    ]