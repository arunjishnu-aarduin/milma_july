from django import forms
from django.utils.dates import MONTHS
from .models import *





class DiaryForm(forms.ModelForm):
    class Meta:
        model=Diary
        fields=('id','name')

class VariantForm(forms.ModelForm):
    class Meta:
        model=Variant
        fields=('name','unit')

class CategoryForm(forms.ModelForm):
    class Meta:
        model=Category
        fields=('code','name','specific_gravity','type')

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=('code','variant','category','rate')

class IssueForm(forms.ModelForm):
    class Meta:
        model=Issue
        fields=('id','name','fat','snf','type')

class CompositionForm(forms.ModelForm):
    class Meta:
        model=Composition
        fields=('category','issue','ratio','method')
class MethodPercentageForm(forms.ModelForm):
    class Meta:
        model=MethodPercentage
        fields=('category','method','percentage')

class IssueAsCategoryForm(forms.ModelForm):
    class Meta:
        model=IssueAsCategory
        fields=('issue','category')

class ActualSaleForm(forms.ModelForm):
    class Meta:
        model=ActualSale
        fields=('month','product','sales')
class ActualSaleFormUnion(forms.ModelForm):
    class Meta:
        model=ActualSale
        fields=('month','product','sales','diary')

class ActualStockinForm(forms.ModelForm):
    class Meta:
        model=ActualStockin
        fields=('month','product','quantity','from_diary')
class ActualStockinFormUnion(forms.ModelForm):
    class Meta:
        model=ActualStockin
        fields=('month','product','quantity','from_diary','diary')

class ProductCategoryGrowthFactorForm(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('category','growth_factor','month')
class ProductCategoryGrowthFactorFormUnion(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('category','growth_factor','month','diary')
class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model=ProductConfiguration
        fields=('product','diary')
class ActualWMProcurementForm(forms.ModelForm):
    class Meta:
        model=ActualWMProcurement
        fields=('month','procurement')
class ActualWMProcurementFormUnion(forms.ModelForm):
    class Meta:
        model=ActualWMProcurement
        fields=('month','procurement','diary')

class ProcurementGrowthFactorForm(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('month','growth_factor')
class ProcurementGrowthFactorFormUnion(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('month','growth_factor','diary')
class IssueRequirementForm(forms.ModelForm):
    #month=forms.ChoiceField(choices=MONTHS.items())
    class Meta:
        model=Composition
        #fields=('issue','month',)
        fields=('issue',)
class IssueRequirementFormBasic(forms.Form):
    #month=forms.ChoiceField(choices=MONTHS.items())
    Issue_Choice=Issue.objects.filter(type='3').exclude(name__in=['ADA','SUGAR'])
    issue=forms.ChoiceField(choices=( (x.id, x.name) for x in Issue_Choice ))
    

class IssueRequirementFormUnion(forms.ModelForm):

    Diary_Choice=Diary.objects.all()
    diary=forms.ChoiceField(choices=( (x.id, x.name) for x in Diary_Choice ))
    class Meta:
        model=Composition
        #fields=('issue','month',)
        fields=('issue','diary',)
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
