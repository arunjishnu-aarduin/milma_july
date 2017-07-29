from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views




urlpatterns=[

    url(r'^issuerequirement/',views.issuerequirement,name='issuerequirement'),
    url(r'^issuerequirementUnion/',views.issuerequirementUnion,name='issuerequirementUnion'),
    url(r'^basicRequirement/',views.basicRequirement,name='basicRequirement'),
    url(r'^basicRequirementUnion/',views.basicRequirementUnion,name='basicRequirementUnion'),
    url(r'^interStockMilkTransferUnion/',views.interStockMilkTransferUnion,name='interStockMilkTransferUnion'),
    url(r'^balancing/',views.balancing,name='balancing'),
    url(r'^balancingUnion/',views.balancingUnion,name='balancingUnion'),
    url(r'^generalCalculation/',views.generalCalculation,name='generalCalculation'),
    url(r'^financialYear/',views.financialYear,name='financialYear'),
    url(r'^wmProcurementRate/',views.wmProcurementRate,name='wmProcurementRate'),




    url(r'^basicRequirementUnionDiaryWise/',views.basicRequirementUnionDiaryWise,name='basicRequirementUnionDiaryWise'),

    url(r'^logout/$', auth_views.logout, {'next_page': '/login/'}, name='logout'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^$', auth_views.login, name='login'),
    url(r'^rawmaterialWise/',views.rawmaterialWise,name='rawmaterialWise'),
    url(r'^rawmaterialWiseUnion/',views.rawmaterialWiseUnion,name='rawmaterialWiseUnion'),
    url(r'^diaryNew/',views.diaryNew,name='diaryNew'),
    url(r'^variantNew/',views.variantNew,name='variantNew'),
    url(r'^categoryNew/',views.categoryNew,name='categoryNew'),
    url(r'^productNew/',views.productNew,name='productNew'),
    url(r'^issueNew/',views.issueNew,name='issueNew'),
    url(r'^compositionNew/',views.compositionNew,name='compositionNew'),
    url(r'^methodpercentageNew/',views.methodpercentageNew,name='methodpercentageNew'),
    url(r'^fatPercentageYield/',views.fatPercentageYield,name='fatPercentageYield'),

    url(r'^issueascategoryNew/',views.issueascategoryNew,name='issueascategoryNew'),
    url(r'^targetYear/',views.targetYear,name='targetYear'),
    url(r'^targetYearUnion/',views.targetYearUnion,name='targetYearUnion'),
    url(r'^home/',views.home,name='home'),
    url(r'^growthfactorentry/',views.growthFactorEntry,name='growthFactorEntry'),
    url(r'^growthfactorentryUnion/',views.growthFactorEntryUnion,name='growthFactorEntryUnion'),
    url(r'^productconfiguration/',views.productConfiguration,name='productConfiguration'),
    url(r'^actualyearentry/',views.actualYearEntry,name='actualYearEntry'),
    url(r'^actualYearEntryUnion/',views.actualYearEntryUnion,name='actualYearEntryUnion'),
    url(r'^accounts/login/$', auth_views.login, name='login'),







]
