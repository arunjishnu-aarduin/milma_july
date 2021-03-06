# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.dates import MONTHS
from django.db.models import Sum, F
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
import datetime

# choices
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
    ('1', 'METHOD1'),
    ('2', 'METHOD2'),

)
# for financial year
year_dropdown = []
for y in range(2016, (datetime.datetime.now().year + 5)):
    year_dropdown.append((y, y))


#############################################################################################################333
# funcions

def validate_positive(value):
    if value < 0:
        raise ValidationError(
            _('%(value)s is not a positive number'),
            params={'value': value},
        )


##################################################################################################################################
# Create your models here.
class Diary(models.Model):
    id = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Variant(models.Model):
    name = models.CharField(max_length=50)
    unit = models.DecimalField(max_digits=12, decimal_places=5, validators=[validate_positive])

    class Meta:
        unique_together = ('name', 'unit',)

    def __str__(self):
        return self.name


class Category(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50)
    specific_gravity = models.DecimalField(max_digits=10, decimal_places=4,
                                           validators=[validate_positive, MinValueValidator(0.0001)])
    type = models.CharField(max_length=1, choices=CATEGORY_CHOICES)

    @property
    def distinctMethodList(self):
        method_list = Composition.objects.filter(category=self).values('method').distinct()
        return method_list

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.DecimalField(max_digits=5, decimal_places=0, validators=[validate_positive], primary_key=True)
    variant = models.ForeignKey('Variant', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=15, decimal_places=2, validators=[validate_positive])

    # class Meta:
    # 	unique_together = ('code','variant', 'category',)

    def __str__(self):
        return str(self.code) + "-" + self.category.name + "-" + self.variant.name


class Issue(models.Model):
    id = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50)
    fat = models.DecimalField(max_digits=7, decimal_places=4, validators=[validate_positive, MaxValueValidator(100)])
    snf = models.DecimalField(max_digits=7, decimal_places=4, validators=[validate_positive, MaxValueValidator(100)])
    type = models.CharField(max_length=1, choices=ISSUE_CHOICES)

    def __str__(self):
        return self.name


class Composition(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    ratio = models.DecimalField(max_digits=20, decimal_places=15, validators=[validate_positive])
    method = models.CharField(max_length=1, choices=METHOD_CHOICES)

    class Meta:
        unique_together = ('category', 'method', 'issue',)

    def save(self, *args, **kwargs):

        if self.category.name == "GHEE" or self.category.name == "BUTTER":
            try:

                issue_as_category = IssueAsCategory.objects.get(category=self.category)

                fat_percentage_yield = FatPercentageYield.objects.get(category=self.category, issue=self.issue,
                                                                      method=self.method)

                ratio_value = (issue_as_category.issue.fat / 100) / (
                    (fat_percentage_yield.percentage / 100) * (self.issue.fat / 100))

                self.ratio = ratio_value
            except Exception as e:
                print e

                self.ratio = 0
        super(Composition, self).save(*args, **kwargs)

    @property
    def issueType(self):
        return self.issue.type

    @property
    def methodPercentage(self):

        method_percentage = MethodPercentage.objects.get(category=self.category, method=self.method)
        if method_percentage != None:
            return method_percentage.percentage
        else:
            return 100

    def __str__(self):
        return self.category.name + "-" + self.issue.name


class MethodPercentage(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    percentage = models.DecimalField(max_digits=3, decimal_places=0,
                                     validators=[validate_positive, MaxValueValidator(100)])

    class Meta:
        unique_together = ('category', 'method', 'percentage',)

    def __str__(self):
        return self.category.name + "-" + str(self.method) + "-" + str(self.percentage)


class IssueAsCategory(models.Model):
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('issue', 'category',)

    def __str__(self):
        return self.issue.name + "-" + self.category.name


class FatPercentageYield(models.Model):
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    method = models.CharField(max_length=1, choices=METHOD_CHOICES)
    percentage = models.DecimalField(max_digits=7, decimal_places=4,
                                     validators=[validate_positive, MaxValueValidator(100)])

    class Meta:
        unique_together = ('issue', 'category', 'method',)

    def save(self, *args, **kwargs):
        super(FatPercentageYield, self).save(*args, **kwargs)
        try:
            category_obj = Composition.objects.get(category=self.category, issue=self.issue, method=self.method)

            category_obj.save()

        except Exception as e:
            print "FatPercentageYield Exception:", e

    def __str__(self):
        return self.issue.name + "-" + self.category.name


class ActualSale(models.Model):
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField()
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    sales = models.PositiveIntegerField()
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')

    class Meta:
        unique_together = ('month', 'product', 'diary', 'year',)

    def __str__(self):
        return str(self.year) + "-" + str(MONTHS[self.month]) + "-" + str(self.product.code) + "-" + str(
            self.diary.name) + "-" + str(self.sales)

    def save(self, *args, **kwargs):

        if self.pk:
            actual_sale_obj = ActualSale.objects.get(pk=self.pk)
            # print str(actual_sale_obj.sales)+"Already exist"+str(self.sales)


            existing_obj_actual_month_category = ActualMonthCategory.objects.get(diary=self.diary, month=self.month,
                                                                                 year=self.year,
                                                                                 category=self.product.category)

            existing_obj_actual_month_category.actual_sale = existing_obj_actual_month_category.actual_sale - actual_sale_obj.sales
            existing_obj_actual_month_category.save(update_fields=['actual_sale'])

        super(ActualSale, self).save(*args, **kwargs)

        try:

            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': F('actual_sale') + self.sales, 'actual_stockin': F('actual_stockin'),
                          'actual_stockout': F('actual_stockout')},
            )
        except  Exception as e:
            print "Exception handled 228 (models)" + str(e)
            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': self.sales, 'actual_stockin': 0, 'actual_stockout': 0},
            )

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
            product_category_growth_factor = ProductCategoryGrowthFactor.objects.get(category=self.product.category,
                                                                                     month=self.month, year=self.year,
                                                                                     diary=self.diary)
            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Sale)"
            return 0

    @property
    def targetSalesQuantity(self):
        return (self.sales + (self.sales * self.growthFactor) / 100)

    # @property
    # def targetSalesUnit(self):
    # 	return self.product.variant.unit*self.targetSalesQuantity
    # changed to add specific_gravity
    @property
    def targetSalesUnit(self):
        return self.product.variant.unit * self.targetSalesQuantity * self.product.category.specific_gravity

    @property
    def targetRevenue(self):
        return self.product.rate * self.targetSalesQuantity


class ActualStockin(models.Model):
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField()
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    from_diary = models.ForeignKey('Diary', on_delete=models.CASCADE, related_name="fromDiary",
                                   verbose_name='from dairy')

    class Meta:
        unique_together = ('diary', 'month', 'product', 'from_diary', 'year',)

    def __str__(self):
        return str(self.year) + "-" + str(MONTHS[self.month]) + "-" + str(self.product.code) + "-" + str(
            self.quantity) + "-" + str(self.from_diary.name) + "->" + str(self.diary.name)

    @property
    def growthFactorStockout(self):
        try:
            product_category_growth_factor = ProductCategoryGrowthFactor.objects.get(category=self.product.category,
                                                                                     month=self.month, year=self.year,
                                                                                     diary=self.diary)

            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Stockout)"
            return 0

    # changed to add specific_gravity

    @property
    def targetStockinQuantity(self):
        return (self.quantity + ((self.quantity * self.growthFactorStockin) / 100))

    @property
    def targetStockinUnit(self):
        return (self.product.variant.unit * self.targetStockinQuantity * self.product.category.specific_gravity)

    @property
    def growthFactorStockin(self):
        try:
            product_category_growth_factor = ProductCategoryGrowthFactor.objects.get(category=self.product.category,
                                                                                     month=self.month, year=self.year,
                                                                                     diary=self.diary)
            return product_category_growth_factor.growth_factor
        except Exception as e:
            print "Growth Factor not exist(Stockin)"
            return 0

    # changed to add specific_gravity
    @property
    def targetStockOutQuantity(self):
        # target_stock_out=ActualStockin.objects.filter(from_diary=self.from_diary,month=self.month,product=self.product).aggregate(actual_stock_out=Coalesce(Sum('quantity'),0))['actual_stock_out']
        # return target_stock_out+((target_stock_out*self.growthFactorStockout)/100)
        return (self.quantity + ((self.quantity * self.growthFactorStockout) / 100))

    @property
    def targetStockoutUnit(self):
        return (self.product.variant.unit * self.targetStockOutQuantity * self.product.category.specific_gravity)

    @property
    def actualStockOut(self):
        actual_stock_out = ActualStockin.objects.filter(from_diary=self.diary, month=self.month, year=self.year,
                                                        product=self.product).aggregate(
            actual_stock_out=Coalesce(Sum('quantity'), 0))['actual_stock_out']
        # the above query will return aggregate of actual stockout
        return actual_stock_out

    # changed to add specific_gravity
    @property
    def actualStockoutQuantity(self):
        variant = self.product.variant
        if variant != None:
            return variant.unit * self.quantity * self.actualStockOut * self.product.category.specific_gravity
        else:
            return 0

    def save(self, *args, **kwargs):

        if self.pk:
            actual_stockin_obj = ActualStockin.objects.get(pk=self.pk, diary=self.diary)
            # print str(actual_sale_obj.sales)+"Already exist"+str(self.sales)


            existing_obj_actual_month_category = ActualMonthCategory.objects.get(diary=self.diary, month=self.month,
                                                                                 year=self.year,
                                                                                 category=self.product.category)

            existing_obj_actual_month_category.actual_stockin = existing_obj_actual_month_category.actual_stockin - actual_stockin_obj.quantity
            existing_obj_actual_month_category.save(update_fields=['actual_stockin'])



            actual_stockout_obj = ActualStockin.objects.get(pk=self.pk, from_diary=self.diary)

            existing_obj_actual_month_category = ActualMonthCategory.objects.get(diary=self.from_diary, month=self.month,
                                                                                 year=self.year,
                                                                                 category=self.product.category)

            existing_obj_actual_month_category.actual_stockout = existing_obj_actual_month_category.actual_stockout - actual_stockout_obj.quantity
            existing_obj_actual_month_category.save(update_fields=['actual_stockout'])

        super(ActualStockin, self).save(*args, **kwargs)

        try:

            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': F('actual_sale'), 'actual_stockin': F('actual_stockin') + self.quantity,
                          'actual_stockout': F('actual_stockout')},
            )
        except  Exception as e:
            print "Exception handled 395 (models)" + str(e)
            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': 0, 'actual_stockin': self.quantity, 'actual_stockout': 0},
            )

        try:

            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.from_diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': F('actual_sale'), 'actual_stockin': F('actual_stockin'),
                          'actual_stockout': F('actual_stockout') + self.quantity},
            )
        except  Exception as e:
            print "Exception handled 411 (models)" + str(e)
            obj_actual_month_category, created = ActualMonthCategory.objects.update_or_create(
                diary=self.from_diary, month=self.month, year=self.year, category=self.product.category,
                defaults={'actual_sale': 0, 'actual_stockin': 0, 'actual_stockout': self.quantity},
            )


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
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    growth_factor = models.DecimalField(max_digits=8, decimal_places=4)
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField(default=datetime.datetime.now().year)
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')

    class Meta:
        unique_together = ('category', 'month', 'diary', 'year',)

    def __str__(self):
        return str(self.year) + "-" + MONTHS[self.month] + "-" + self.category.name + "-" + self.diary.name


class ProductConfiguration(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')

    class Meta:
        unique_together = ('product', 'diary',)

    def __str__(self):
        return str(self.product) + "-" + self.diary.name


class ActualWMProcurement(models.Model):
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField()
    procurement = models.DecimalField(max_digits=20, decimal_places=2, validators=[validate_positive])
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')

    class Meta:
        unique_together = ('month', 'diary', 'year',)

    def __str__(self):
        return str(self.year) + "-" + MONTHS[self.month] + "-" + self.diary.name + "-" + str(self.procurement)

    @property
    def growthFactor(self):
        try:
            procurement_growth_factor = ProcurementGrowthFactor.objects.get(month=self.month, year=self.year,
                                                                            diary=self.diary)

            return procurement_growth_factor.growth_factor
        except Exception as e:
            print "Procurement Growth Factor not exist"
            return 0

    @property
    def targetProcurement(self):
        try:
            specific_gravity = Category.objects.get(name="WM").specific_gravity
            return ((self.procurement + (self.procurement * self.growthFactor) / 100) * specific_gravity)
        except Exception as e:
            print "Specific Gravity Fetching Failed"
            return (self.procurement + (self.procurement * self.growthFactor) / 100)

    @property
    def targetProcurementLitre(self):
        try:
            return (self.procurement + (self.procurement * self.growthFactor) / 100)
        except Exception as e:
            print "Exception Handled At targetProcurementLitre 370"
            return 0

    @property
    def targetAmount(self):
        try:
            rate = ConfigurationAttribute.objects.first().wm_procurement_rate
            return self.targetProcurementLitre * rate
        except Exception as e:
            print "Wm Procurement Rate Fetching Failed"
            return 0


class ProcurementGrowthFactor(models.Model):
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField(default=datetime.datetime.now().year)
    growth_factor = models.DecimalField(max_digits=8, decimal_places=4)
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')

    class Meta:
        unique_together = ('month', 'diary', 'year',)

    def __str__(self):
        return str(self.year) + "-" + MONTHS[self.month] + "-" + self.diary.name


class UserDiaryLink(models.Model):
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.user.username


class IssueRequirement(models.Model):
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    year = models.PositiveSmallIntegerField()
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    requirement = models.DecimalField(max_digits=20, decimal_places=6)

    def __str__(self):
        return str(self.diary.name) + "-" + str(MONTHS[self.month]) + "-" + str(self.year) + "-" + str(
            self.issue.name) + "-" + str(self.requirement)


class InterStockMilkTransferOrder(models.Model):
    from_diary = models.ForeignKey('Diary', on_delete=models.CASCADE, related_name="from_Diary",
                                   verbose_name='from dairy')
    to_diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')
    priority = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('from_diary', 'to_diary',)

    def __str__(self):
        return str(self.from_diary.name) + "->" + str(self.to_diary.name) + "-" + str(self.priority)


class InterStockCreamTransferOrder(models.Model):
    from_diary = models.ForeignKey('Diary', on_delete=models.CASCADE, related_name="from_dairy",
                                   verbose_name='from dairy')
    to_diary = models.ForeignKey('Diary', on_delete=models.CASCADE, verbose_name='dairy')
    priority = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('from_diary', 'to_diary',)

    def __str__(self):
        return str(self.from_diary.name) + "->" + str(self.to_diary.name) + "-" + str(self.priority)


class GeneralCalculation(models.Model):
    code = models.PositiveSmallIntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=12, decimal_places=4)

    def __str__(self):
        return str(self.code) + " " + str(self.name) + " " + str(self.value)


class ConfigurationAttribute(models.Model):
    issue_requirement_change_status = models.BooleanField()
    wm_procurement_rate = models.DecimalField(max_digits=15, decimal_places=2, validators=[validate_positive],
                                              verbose_name="rate")

    def __str__(self):
        return str(self.financial_Year) + " Composition Status-" + str(
            self.issue_requirement_change_status) + " WM Procurement Rate-" + str(self.wm_procurement_rate)


class IssueUsedAsCategoryIndirect(models.Model):
    issue = models.ForeignKey('Issue', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('issue', 'category',)

    def __str__(self):
        return str(self.issue.name) + "-" + str(self.category.name)

        #
        # class FetchLog(models.Model):
        #     user=models.ForeignKey(User,)
        #
        #


class ActualMonthCategory(models.Model):
    year = models.PositiveSmallIntegerField()
    diary = models.ForeignKey('Diary', on_delete=models.CASCADE)
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    actual_sale = models.PositiveIntegerField()
    actual_stockin = models.PositiveIntegerField()
    actual_stockout = models.PositiveIntegerField()

    def __str__(self):
        return str(self.year) + "-" + str(self.category.name) + "-" + str(self.month)
