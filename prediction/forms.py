from django import forms
from .models import Diary,Variant,Category,Product,Issue,Composition,MethodPercentage,IssueAsCategory,ActualSale,ActualStockin,ProductCategoryGrowthFactor,ProductConfiguration,ActualWMProcurement,ProcurementGrowthFactor

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
        fields=('month','product','sales','diary')

class ActualStockinForm(forms.ModelForm):
    class Meta:
        model=ActualStockin
        fields=('month','product','quantity','from_diary')

class ProductCategoryGrowthFactorForm(forms.ModelForm):
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
        fields=('month','procurement','diary')

class ProcurementGrowthFactorForm(forms.ModelForm):
    class Meta:
        model=ProcurementGrowthFactor
        fields=('month','growth_factor','diary')
class IssueRequirementForm(forms.ModelForm):
    class Meta:
        model=Composition
        fields=('issue',)

class CategoryWiseRequirementForm(forms.ModelForm):
    class Meta:
        model=ProductCategoryGrowthFactor
        fields=('month','category')
