from django.conf.urls import url
from . import views


urlpatterns=[
    url(r'^issuerequirement',views.issuerequirement,name='issuerequirement'),
    url(r'^rawmaterialWise',views.rawmaterialWise,name='rawmaterialWise'),
    url(r'^diaryNew/',views.diaryNew,name='diaryNew'),
    url(r'^variantNew/',views.variantNew,name='variantNew'),
    url(r'^categoryNew/',views.categoryNew,name='categoryNew'),
    url(r'^productNew/',views.productNew,name='productNew'),
    url(r'^issueNew/',views.issueNew,name='issueNew'),
    url(r'^compositionNew/',views.compositionNew,name='compositionNew'),
    url(r'^methodpercentageNew/',views.methodpercentageNew,name='methodpercentageNew'),
    url(r'^issueascategoryNew/',views.issueascategoryNew,name='issueascategoryNew'),
    url(r'^actualsaleNew/',views.actualsaleNew,name='actualsaleNew'),
    url(r'^actualstockinNew/',views.actualstockinNew,name='actualstockinNew'),
    url(r'^productcategorygrowthfactorNew/',views.productcategorygrowthfactorNew,name='productcategorygrowthfactorNew'),
    url(r'^productconfigurationNew/',views.productconfigurationNew,name='productconfigurationNew'),
    url(r'^actualWMProcurementNew/',views.actualWMProcurementNew,name='actualWMProcurementNew'),
    url(r'^procurementgrowthfactorNew/',views.procurementgrowthfactorNew,name='procurementgrowthfactorNew'),



]
