# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Diary)
admin.site.register(Variant)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Issue)
admin.site.register(Composition)
admin.site.register(MethodPercentage)
admin.site.register(IssueAsCategory)
admin.site.register(ActualSale)
admin.site.register(ActualStockin)
admin.site.register(ProductCategoryGrowthFactor)
admin.site.register(ProductConfiguration)
admin.site.register(ActualWMProcurement)
admin.site.register(ProcurementGrowthFactor)
admin.site.register(UserDiaryLink)
admin.site.register(FatPercentageYield)
admin.site.register(InterStockMilkTransferOrder)
admin.site.register(InterStockCreamTransferOrder)
admin.site.register(IssueRequirement)
admin.site.register(GeneralCalculation)
admin.site.register(ConfigurationAttribute)
admin.site.register(IssueUsedAsCategoryIndirect)
admin.site.register(ActualMonthCategory)
