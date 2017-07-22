from django import forms
from django.utils.dates import MONTHS
from .models import *
from django.core.validators import MaxLengthValidator,MaxValueValidator,MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

#Choices

VARIANT_CHOICES = (
	('Kg', 'Kg'),
	('mg', 'mg'),
    ('L', 'L'),
    ('ml', 'ml'),
    ('g','g'),

)


#funcions

def validate_positive(value):
    if value < 0:
        raise ValidationError(
            _('%(value)s is not a positive number'),
            params={'value': value},
        )



class DiaryForm(forms.ModelForm):
    class Meta:
        model=Diary
        fields=('id','name')

class VariantForm(forms.ModelForm):
    first_name=forms.FloatField(validators=[validate_positive])
    unit_name=forms.ChoiceField(choices=VARIANT_CHOICES)
    class Meta:
        model=Variant

        fields=('first_name','unit_name','unit',)
    def validate_unique(self):
        pass

class CategoryForm(forms.ModelForm):
    class Meta:
        model=Category
        fields=('code','name','specific_gravity','type')

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=('code','category','variant','rate')
    def validate_unique(self):
        pass

class IssueForm(forms.ModelForm):
    fat=forms.DecimalField(max_digits=7,decimal_places=4,validators=[validate_positive,MaxValueValidator(100)])
    snf=forms.DecimalField(max_digits=7,decimal_places=4,validators=[validate_positive,MaxValueValidator(100)])
    class Meta:
        model=Composition
        fields=('issue','fat','snf',)

class CompositionForm(forms.ModelForm):
    class Meta:
        model=Composition
        fields=('category','issue','ratio','method')
    def validate_unique(self):
        pass
class MethodPercentageForm(forms.ModelForm):
    class Meta:
        model=MethodPercentage
        fields=('category','method','percentage')
    def validate_unique(self):
        pass
class FatPercentageYieldForm(forms.ModelForm):
    class Meta:
        model=FatPercentageYield
        fields=('category','issue','method','percentage')
    def validate_unique(self):
        pass

class IssueAsCategoryForm(forms.ModelForm):
    class Meta:
        model=IssueAsCategory
        fields=('issue','category')

class ActualSaleForm(forms.ModelForm):

    class Meta:
        model=ActualSale
        fields=('month','product','sales')
    def validate_unique(self):
        pass
class ActualSaleFormUnion(forms.ModelForm):
    class Meta:
        model=ActualSale
        fields=('diary','month','product','sales')
    def validate_unique(self):
        pass

class ActualStockinForm(forms.ModelForm):

    class Meta:
        model=ActualStockin
        fields=('month','product','quantity','from_diary')
    def validate_unique(self):
        pass
class ActualStockinFormUnion(forms.ModelForm):
    class Meta:
        model=ActualStockin
        fields=('month','product','quantity','from_diary','diary')
    def validate_unique(self):
        pass
class ProductCategoryGrowthFactorForm(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('month','category','growth_factor')
    def validate_unique(self):
        pass

class ProductCategoryGrowthFactorFormUnion(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('diary','month','category','growth_factor')
    def validate_unique(self):
        pass
class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model=ProductConfiguration
        fields=('product','diary')
    def validate_unique(self):
        pass
class ActualWMProcurementForm(forms.ModelForm):
    class Meta:
        model=ActualWMProcurement
        fields=('month','procurement')
    def validate_unique(self):
        pass
class ActualWMProcurementFormUnion(forms.ModelForm):
    class Meta:
        model=ActualWMProcurement
        fields=('diary','month','procurement')
    def validate_unique(self):
        pass

class ProcurementGrowthFactorForm(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('month','growth_factor')
    def validate_unique(self):
        pass
class ProcurementGrowthFactorFormUnion(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('diary','month','growth_factor')
    def validate_unique(self):
        pass
class IssueRequirementForm(forms.ModelForm):
    #month=forms.ChoiceField(choices=MONTHS.items())
    class Meta:
        model=Composition
        #fields=('issue','month',)
        fields=('issue',)
class IssueRequirementFormBasic(forms.Form):
    # month=forms.ChoiceField(choices=MONTHS.items())
    Issue_Choice=Issue.objects.filter(type='3').exclude(name__in=['ADA','SUGAR'])
    issue=forms.ChoiceField(choices=( (x.id, x.name) for x in Issue_Choice ))
class IssueRequirementFormBasicUnion(forms.ModelForm):
        #month=forms.ChoiceField(choices=MONTHS.items())
    Issue_Choice=Issue.objects.filter(type='3').exclude(name__in=['ADA','SUGAR'])
    issue=forms.ChoiceField(choices=( (x.id, x.name) for x in Issue_Choice ))
    class Meta:
        model=ProcurementGrowthFactor
        fields=('diary','issue',)

class IssueRequirementFormUnion(forms.ModelForm):

    Diary_Choice=Diary.objects.all()
    dairy=forms.ChoiceField(choices=( (x.id, x.name) for x in Diary_Choice ))
    class Meta:
        model=Composition
        #fields=('issue','month',)
        fields=('issue','dairy',)

class CategoryWiseRequirementForm(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('month','category')
class CategoryWiseRequirementFormUnion(forms.ModelForm):
    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        #print str(exclude)
        #exclude.remove('problem') # allow checking against the missing attribute

        try:
            self.instance.validate_unique(exclude=exclude)
        except ValidationError, e:
            print "unique_together exception handled in CategoryWiseRequirementFormUnion"
            pass
            #self._update_errors(e.message_dict)
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('month','category','diary')
class MonthOnlyForm(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('month',)