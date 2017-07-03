# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxLengthValidator,MaxValueValidator,MinValueValidator
from django.db import models
from django.utils.dates import MONTHS
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User


#choices
ISSUE_CHOICES = (
    ('1', 'TYPE 1'),
    ('2', 'TYPE 2'),
    ('3', 'TYPE 3'),

)
CATEGORY_CHOICES = (
    ('M', 'Milk'),
    ('O', 'Other'),

)
METHOD_CHOICES = (
    ('1','METHOD1'),
    ('2','METHOD2'),



)
#############################################################################################################333
#funcions

def validate_positive(value):
    if value < 0:
        raise ValidationError(
            _('%(value)s is not a positive number'),
            params={'value': value},
        )


##################################################################################################################################
# Create your models here.
class Diary(models.Model):
    id=models.CharField(max_length=5,primary_key=True)
    name=models.CharField(max_length=50)
    def __str__(self):
        return self.id+"-"+self.name
class Variant(models.Model):
    name=models.CharField(max_length=50)
    unit=models.PositiveSmallIntegerField()
    def __str__(self):
		return self.name
class Category(models.Model):
    code=models.CharField(max_length=3,primary_key=True)
    name=models.CharField(max_length=50)
    specific_gravity=models.DecimalField(max_digits=10,decimal_places=4,validators=[validate_positive,MinValueValidator(0.0001)])
    type=models.CharField(max_length=1,choices=CATEGORY_CHOICES)
    @property
    def distinctMethodList(self):
        method_list=Composition.objects.filter(category=self).values('method').distinct()
        return method_list

    def __str__(self):
        return self.code+"-"+self.name

class Product(models.Model):
    code=models.DecimalField(max_digits=5,decimal_places=0,validators=[validate_positive],primary_key=True)
    variant=models.ForeignKey('Variant',on_delete=models.CASCADE)
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    rate=models.DecimalField(max_digits=15,decimal_places=2,validators=[validate_positive])

    def __str__(self):
        return str(self.code)+"-"+self.category.name+"-"+self.variant.name

class Issue(models.Model):
    id=models.CharField(max_length=3,primary_key=True)
    name=models.CharField(max_length=50)
    fat=models.DecimalField(max_digits=5,decimal_places=4,validators=[validate_positive])
    snf=models.DecimalField(max_digits=5,decimal_places=4,validators=[validate_positive])
    type=models.CharField(max_length=1,choices=ISSUE_CHOICES)

    def __str__(self):
        return self.id+"-"+self.name
class Composition(models.Model):
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    issue=models.ForeignKey('Issue',on_delete=models.CASCADE)
    ratio=models.DecimalField(max_digits=20,decimal_places=15,validators=[validate_positive])
    method=models.CharField(max_length=1,choices=METHOD_CHOICES)

    @property
    def issueType(self):
        return self.issue.type
    @property
    def methodPercentage(self):
        method_percentage=MethodPercentage.objects.get(category=self.category,method=self.method)
        if method_percentage != None:
            return method_percentage.percentage
        else:
            return 100
    def __str__(self):
        return self.category.name+"-"+self.issue.name
class MethodPercentage(models.Model):
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    method=models.CharField(max_length=1,choices=METHOD_CHOICES)
    percentage=models.DecimalField(max_digits=3,decimal_places=0,validators=[validate_positive,MaxValueValidator(100)])

    def __str__(self):
        return self.category.name+"-"+str(self.method)+"-"+str(self.percentage)
class IssueAsCategory(models.Model):
    issue=models.ForeignKey('Issue',on_delete=models.CASCADE)
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    def __str__(self):
        return self.issue.name+"-"+self.category.name
class ActualSale(models.Model):
    month=models.PositiveSmallIntegerField(choices=MONTHS.items())
    product=models.ForeignKey('Product',on_delete=models.CASCADE)
    sales=models.PositiveIntegerField()
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)

    def __str__(self):
        return MONTHS[self.month]+"-"+str(self.product.code)+"-"+self.diary.name+"-"+str(self.sales)
    @property
    def growthFactor(self):
        """
        product_category_growth_factor=ProductCategoryGrowthFactor.objects.get(category=self.product.category,month=self.month,diary=self.diary)

        if product_category_growth_factor!=None:
            return product_category_growth_factor.growth_factor
        else:
            return 0
            """
        try:
            product_category_growth_factor=ProductCategoryGrowthFactor.objects.get(category=self.product.category,month=self.month,diary=self.diary)
            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Sale)"
            return 0
    @property
    def targetSalesQuantity(self):
        return (self.sales+(self.sales*self.growthFactor)/100)
    @property
    def targetSalesUnit(self):
        return self.product.variant.unit*self.targetSalesQuantity
    @property
    def targetRevenue(self):
        return self.product.rate*self.targetSalesQuantity


class ActualStockin(models.Model):
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    month=models.PositiveSmallIntegerField(choices=MONTHS.items())
    product=models.ForeignKey('Product',on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    from_diary=models.ForeignKey('Diary',on_delete=models.CASCADE,related_name="fromDiary")
    def __str__(self):
        return MONTHS[self.month]+"-"+str(self.product.code)+"-"+str(self.quantity)+"-"+self.from_diary.name+"->"+self.diary.name


    @property
    def growthFactorStockout(self):
        try:
            product_category_growth_factor=ProductCategoryGrowthFactor.objects.get(category=self.product.category,month=self.month,diary=self.diary)

            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Stockout)"
            return 0



    @property
    def targetStockinQuantity(self):
        return (self.quantity+((self.quantity*self.growthFactorStockin)/100))
    @property
    def targetStockinUnit(self):
        return (self.product.variant.unit*self.targetStockinQuantity)



    @property
    def growthFactorStockin(self):
        try:
            product_category_growth_factor=ProductCategoryGrowthFactor.objects.get(category=self.product.category,month=self.month,diary=self.from_diary)
            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Stockin)"
            return 0
    @property
    def targetStockOutQuantity(self):
        #target_stock_out=ActualStockin.objects.filter(from_diary=self.from_diary,month=self.month,product=self.product).aggregate(actual_stock_out=Coalesce(Sum('quantity'),0))['actual_stock_out']
        #return target_stock_out+((target_stock_out*self.growthFactorStockout)/100)
        return (self.quantity+((self.quantity*self.growthFactorStockout)/100))
    @property
    def targetStockoutUnit(self):
        return (self.product.variant.unit*self.targetStockOutQuantity)

    @property
    def actualStockOut(self):
        actual_stock_out=ActualStockin.objects.filter(from_diary=self.diary,month=self.month,product=self.product).aggregate(actual_stock_out=Coalesce(Sum('quantity'),0))['actual_stock_out']
        #the above query will return aggregate of actual stockout
        return actual_stock_out
    @property
    def actualStockoutQuantity(self):
        variant=self.product.variant
        if variant != None:
            return variant.unit*self.quantity*self.actualStockOut
        else:
            return 0
"""
    @property
    def targetStockoutQuantity(self):
        variant=self.product.variant
        if variant != None:
            return variant.unit*self.quantity*self.targetStockOut
        else:
            return 0
"""
class ProductCategoryGrowthFactor(models.Model):
    category=models.ForeignKey('Category',on_delete=models.CASCADE)
    growth_factor=models.DecimalField(max_digits=3,decimal_places=0,validators=[validate_positive,MaxValueValidator(100)])
    month=models.PositiveSmallIntegerField(choices=MONTHS.items())
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    def __str__(self):
        return MONTHS[self.month]+"-"+self.category.name+"-"+self.diary.name

class ProductConfiguration(models.Model):
    product=models.ForeignKey('Product',on_delete=models.CASCADE)
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    def __str__(self):
        return self.product.name+"-"+self.diary.name

class ActualWMProcurement(models.Model):
    month=models.PositiveSmallIntegerField(choices=MONTHS.items())
    procurement=models.DecimalField(max_digits=20,decimal_places=2,validators=[validate_positive])
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    def __str__(self):
        return MONTHS[self.month]+"-"+self.diary.name+"-"+str(procurement)

class ProcurementGrowthFactor(models.Model):
    month=models.PositiveSmallIntegerField(choices=MONTHS.items())
    growth_factor=models.DecimalField(max_digits=3,decimal_places=0,validators=[validate_positive,MaxValueValidator(100)])
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    def __str__(self):
        return MONTHS[self.month]+"-"+self.diary.name
class UserDiaryLink(models.Model):
    diary=models.ForeignKey('Diary',on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE,primary_key=True)
    def __str__(self):
        return self.user.username
