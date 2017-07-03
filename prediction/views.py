# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .forms import DiaryForm,VariantForm,CategoryForm,ProductForm,IssueForm,CompositionForm,MethodPercentageForm,IssueAsCategoryForm,ActualSaleForm,ActualStockinForm,ProductCategoryGrowthFactorForm,ProductConfigurationForm,ActualWMProcurementForm,ProcurementGrowthFactorForm,IssueRequirementForm,CategoryWiseRequirementForm
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render
#from .models import Variant,Product,ProductCategoryGrowthFactor,Composition,Issue,ActualStockin,ActualSale,Diary,Category,MethodPercentage,IssueAsCategory,UserDiaryLink
from .models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.utils.dates import MONTHS

# Create your views here.
def diary_of_user(user):
    try:
        user_diary_link_obj=UserDiaryLink.objects.get(user=user)
    except UserDiaryLink.DoesNotExist:
        diary=None
    return user_diary_link_obj.diary
def getMethodPercentage(category,method):
    method_list=category.distinctMethodList
    method_percentage_list=MethodPercentage.objects.filter(category=category,method=method)

    #Method Percentage Validation
    print "Method Count from Comopsition:"+str(method_list.count())
    print "Method Count from MethodPercentage:",MethodPercentage.objects.filter(category=category).count()
    if (MethodPercentage.objects.filter(category=category).count()!=method_list.count()) and method_list.count()!=1:

        return 0

    if len(method_percentage_list) ==0:
        return 100
    else:
        return method_percentage_list[0].percentage


def diaryNew(request):

    if request.method == "POST":
        form = DiaryForm(request.POST)
        if form.is_valid():
            diary = form.save(commit=False)
            diary.save()
            return HttpResponse("inserted")
    else:
        form = DiaryForm()
    return render(request, 'prediction/all_new.html', {'form': form,'name':"Diary"})

def issuerequirement(request):
    if request.method == "POST":
        form = IssueRequirementForm(request.POST)
        if form.is_valid():
            #diary = form.save(commit=False)
            #diary.save()

            issue=form.cleaned_data["issue"]

            CategoryList=Category.objects.all()
            issue_requirement=0
            global requested_issue
            for category in CategoryList:

                print category.name
                saledetails=ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=4,diary='CPD')

                stockindetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=4,diary='CPD')

                stockoutdetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=4,from_diary='CPD')

                salesum=0
                stockout=0
                stockin=0
                for sale in saledetails:

                    print "\t"+str(sale.product.code)+"-"+sale.product.category.name
                    print "\tsale-"+str(sale.targetSalesQuantity)
                    salesum+=sale.targetSalesQuantity
                for stock in stockindetail:
                    print "\t"+str(stock.product.code)+"-"+sale.product.category.name
                    print "\tstockin-"+(stock.targetStockinQuantity)
                    stockin+=stock.targetStockinQuantity

                for stock in stockoutdetail:
                    print "\t"+str(stock.product.code)+"-"+sale.product.category.name
                    print "\tstockout-"+str(stock.targetStockoutQuantity)
                    stockout+=stock.targetStockoutQuantity

                print "\tsales",salesum
                print "\tstockout",stockout
                print "\tstockin",stockin
                target=(salesum+stockout-(stockin))
                print "\tRequired issue  "+issue.name
                requested_issue=issue
                print "\tTarget",target
                issue_requirement+=requireIssue(category,target)
                print "issue_requirement",issue_requirement
            return render(request, "prediction/issue.html",{"issuerequirement":issue_requirement,"issue":issue.name})

    else:
        form = IssueRequirementForm()
    return render(request, 'prediction/issue_requirement.html', {'form': form})
def variantNew(request):

    if request.method == "POST":
        form = VariantForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.save()
            return HttpResponse("inserted")
    else:
        form = VariantForm()
    return render(request, 'prediction/all_new.html', {'form': form,'name':"Diary"})

def categoryNew(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category=form.save(commit=False)
            category.save()
            return HttpResponse("inserted")
    else:
        form=CategoryForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Category"})

def productNew(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product=form.save(commit=False)
            product.save()
            return HttpResponse("inserted")
    else:
        form=ProductForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Product"})

def issueNew(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product=form.save(commit=False)
            product.save()
            return HttpResponse("inserted")
    else:
        form=ProductForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Product"})

def compositionNew(request):
    if request.method == "POST":
        form = CompositionForm(request.POST)
        if form.is_valid():
            composition=form.save(commit=False)
            composition.save()
            return HttpResponse("inserted")
    else:
        form=CompositionForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Composition"})

def methodpercentageNew(request):
    if request.method == "POST":
        form = MethodPercentageForm(request.POST)
        if form.is_valid():
            method_percentage=form.save(commit=False)
            method_percentage.save()
            return HttpResponse("inserted")
    else:
        form=MethodPercentageForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Method Percentage"})

def issueascategoryNew(request):
    if request.method == "POST":
        form = IssueAsCategoryForm(request.POST)
        if form.is_valid():
            issue_as_category=form.save(commit=False)
            issue_as_category.save()
            return HttpResponse("inserted")
    else:
        form=IssueAsCategoryForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Issue As Category"})


def actualsaleNew(request):
    if request.method == "POST":
        form = ActualSaleForm(request.POST)
        if form.is_valid():
            actual_sale=form.save(commit=False)
            actual_sale.save()
            return HttpResponse("inserted")
    else:
        form=ActualSaleForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Actual Sale"})

def actualstockinNew(request):
    if request.method == "POST":
        form = ActualStockinForm(request.POST)
        if form.is_valid():
            actual_stock_in=form.save(commit=False)
            actual_stock_in.save()
            return HttpResponse("inserted")
    else:
        form=ActualStockinForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Actual Stockin"})

def productcategorygrowthfactorNew(request):
    diary=diary_of_user(request.user)
    productGrowthFactor=ProductCategoryGrowthFactor.objects.filter(diary=diary).order_by('month','category')
    if request.method == "POST":
        form = ProductCategoryGrowthFactorForm(request.POST)
        if form.is_valid():
            product_category_growth_factor=form.save(commit=False)
            product_category_growth_factor.save()
            return HttpResponseRedirect(request,'prediction/GrowthFactorEntry.html',{'form':form,'productGrowthFactor':productGrowthFactor,'MONTHS':MONTHS})
    else:
        form=ProductCategoryGrowthFactorForm()
    #return render(request,'prediction/all_new.html',{'form':form,'name':"Product Category Growth Factor"})
    return render(request,'prediction/GrowthFactorEntry.html',{'form':form,'productGrowthFactor':productGrowthFactor,'MONTHS':MONTHS})

def productconfigurationNew(request):
    if request.method == "POST":
        form = ProductConfigurationForm(request.POST)
        if form.is_valid():
            product_configuration=form.save(commit=False)
            product_configuration.save()
            return HttpResponse("inserted")
    else:
        form=ProductConfigurationForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Product Configuration"})

def actualWMProcurementNew(request):
    if request.method == "POST":
        form = ActualWMProcurementForm(request.POST)
        if form.is_valid():
            actual_wm_procurement=form.save(commit=False)
            actual_wm_procurement.save()
            return HttpResponse("inserted")
    else:
        form=ActualWMProcurementForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Actual WM Procurement"})

def procurementgrowthfactorNew(request):
    if request.method == "POST":
        form = ProcurementGrowthFactorForm(request.POST)
        if form.is_valid():
            procurement_growth_factor=form.save(commit=False)
            procurement_growth_factor.save()
            return HttpResponse("inserted")
    else:
        form=ProcurementGrowthFactorForm()
    return render(request,'prediction/all_new.html',{'form':form,'name':"Procurement Growth Factor"})

def requireIssue(category,sale_in_unit):
    #methodlist=Composition.objects.distinct().filter(cat_id_id=cat_id)

    method_list=Composition.objects.filter(category=category).values('method').distinct()

    global target_unit
    global target_inner


    target_method=0
    for method in method_list:
        print "\t\tmethod"+method['method']
        composition_list=Category.objects.get(code=category.code).composition_set.filter(method=method['method'])
        target_composition=0
        print composition_list
        for composition in composition_list:
            print "\t\t"+composition.issue.name
            target_unit=0
            target_inner=0
            if composition.issue==requested_issue:
                print "\t\t\tmatch"
                target_unit+=composition.ratio*sale_in_unit*(composition.methodPercentage/100)
                print "\t\t\ttarget_unit",target_unit
            elif composition.issueType=='1':
                print "\t\t\ttype1"
                new_category=IssueAsCategory.objects.get(issue=composition.issue)
                new_sale_in_unit=sale_in_unit*composition.ratio
                print "\t\t\tnew_category "+new_category.category.name
                print "\t\t\tnew_sale_in_unit",new_sale_in_unit
                target_inner+=requireIssue(new_category.category,new_sale_in_unit)
                print "\t\t\ttarget_inner",target_inner

            else :
                print "\t\t\t\tnot match"

            target_composition+=(target_unit+target_inner)
            print "\t\t\t\tComposition_sum",target_composition
        target_method+=target_composition
    return target_method

def rawmaterialWise(request):
    if request.method == "POST":
        form = CategoryWiseRequirementForm(request.POST)
        if form.is_valid():
            sale_details=[]
            composdetails=[]
            compos2details=[]
            category=form.cleaned_data["category"]
            category_name=category.name
            month=form.cleaned_data["month"]

            diary=diary_of_user(request.user)
            if diary==None:
                return HttpResponse("User Not Linked With Diary")

            Compos=Category.objects.get(name=category_name).composition_set.filter(method='1').all()
            product_list=Category.objects.get(name=category_name).product_set.all()

            #product_sales_list=ActualSale.objects.filter(product.category=category,month=month,diary=diary)
            productlist_of_category=category.product_set.all()
            if productlist_of_category.exists():
                #return HttpResponse(product_sales_list)
                product_sales_list=ActualSale.objects.filter(product__in=productlist_of_category,month=month,diary=diary)
                target_sale_unit_of_category=0
                if len(product_sales_list)==0:
                    #return HttpResponse("No Sales Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
                    print "No Sales Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name)
                else:
                    for sale in product_sales_list:
                        target_sale_unit_of_category+=sale.targetSalesUnit
                print "sale-",target_sale_unit_of_category

                product_stockin_list=ActualStockin.objects.filter(product__in=productlist_of_category,month=month,diary=diary)
                target_stockin_unit_of_category=0
                if len(product_stockin_list)==0:
                    #return HttpResponse("No Sales Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
                    print "No Stockin Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name)
                else:
                    for stockin in product_stockin_list:
                        target_stockin_unit_of_category+=stockin.targetStockinUnit
                print "stockin-",target_stockin_unit_of_category
                #Stockin over



                product_stockout_list=ActualStockin.objects.filter(product__in=productlist_of_category,month=month,from_diary=diary)
                target_stockout_unit_of_category=0
                if len(product_stockout_list)==0:
                    #return HttpResponse("No Sales Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
                    print "No Stockout Available for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name)
                else:
                    for stockout in product_stockout_list:
                        target_stockout_unit_of_category+=stockout.targetStockoutUnit
                print "stockout-",target_stockout_unit_of_category
                #Stockout over




                target_unit=(target_sale_unit_of_category+target_stockout_unit_of_category)-target_stockin_unit_of_category

                if target_unit==0:
                    return HttpResponse("Netvalue is zero(Stockout+Sale-Stockin=0) for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))

                print "target-",target_unit

                specific_gravity=category.specific_gravity
                target_unit_in_gram=target_unit*specific_gravity
                print "target_unit_in_gram",target_unit_in_gram

                method_list=category.distinctMethodList







                if len(method_list)==0:
                    return HttpResponse("No production methods are available for this category:"+str(category.name)+" ,Please Enter Values in Composition ")
                else:
                    resultitem=[]
                    for method in method_list:
                        print "method+",method['method']


                        methodPercentage=getMethodPercentage(category,method['method'])
                        if methodPercentage==0:
                            return HttpResponse("Please Verify your MethodPercentage")
                        print "Method Percentage:",methodPercentage


                        portion_of_target_unit_in_gram_through_this_method=target_unit_in_gram*(methodPercentage/100)
                        issues=[]
                        resultitem={"method":method,"portion_through_the_method":portion_of_target_unit_in_gram_through_this_method,"method_percentage":methodPercentage,"issue_required":issues}

                        composition_list=Composition.objects.filter(category=category,method=method['method'])

                        for composition in composition_list:
                            issues=[composition.issue.name,portion_of_target_unit_in_gram_through_this_method*composition.ratio]

                            resultitem["issue_required"].append(issues)

                    print resultitem
                    return render(request, "prediction/rawmaterial.html", {"resultitem":resultitem})
            else:
                return HttpResponse("You have not configured any product for category:"+category.name)
    else:
        form = CategoryWiseRequirementForm()
    return render(request, 'prediction/categorywise.html', {'form': form})
"""


            actualsales=ActualSale.objects.all()
            TotalQuantity=0
            ismethod2=Category.objects.get(name=category_name).composition_set.filter(method='2').exists()


            for item in product_list:
#try-catch needed to avoid 'doesn't exist query

                sale_quantity=0
                stockin_quantity=0
                stockout_quantity=0
                try:
                    sale=ActualSale.objects.get(product=item,month=month,diary='CPD')
                    sale_quantity=sale.targetSalesQuantity
                except Exception as e:
                    pass
                try:
                    stockin=ActualStockin.objects.get(product=item,month=month,diary='CPD')
                    stockin_quantity=stockin.targetStockinQuantity
                except Exception as e:
                    pass
                try:
                    stockout=ActualStockin.objects.get(product=item,month=month,from_diary='CPD')
                    stockout_quantity=stockout.targetStockoutQuantity
                except Exception as e:
                    pass

                totalquant=(sale_quantity+stockout_quantity-(stockin_quantity))
                TotalQuantity+=totalquant

                temp={"productname":item.code,"Sales":sale,"TotalQuantity":totalquant
                }
                sale_details.append(temp)
            meth1Total_Quantity=TotalQuantity
            if ismethod2:
                meth2percentage=Category.objects.get(name=category_name).methodpercentage_set.filter(method='2').values()[0]['percentage']
                meth1percentage=Category.objects.get(name=category_name).methodpercentage_set.filter(method='1').values()[0]['percentage']
                meth1Total_Quantity=(TotalQuantity*meth1percentage)/100
                meth2Total_Quantity=(TotalQuantity*meth2percentage)/100
                Composition_method2=Category.objects.get(name=category_name).composition_set.filter(method='2').all()
                for item in Composition_method2:
                        issuename=item.issue.name
                        quantity=item.ratio*meth2Total_Quantity
                        temp={"issuename":issuename,"quantity":quantity}
                        compos2details.append(temp)
            for item in Compos:
                issuename=item.issue.name
                quantity=item.ratio*meth1Total_Quantity
                temp={"issuename":issuename,"quantity":quantity}
                composdetails.append(temp)


            return render(request, "prediction/rawmaterial.html", {"actualsales":sale_details,"netvalue":TotalQuantity
            ,"composition":composdetails,"composition2":compos2details,"method2":ismethod2})
            #return render(request, "mylaw/hello.html", {"product" : json.dumps(product_name[0]['pid'])})

    else:
        form = CategoryWiseRequirementForm()
    return render(request, 'prediction/categorywise.html', {'form': form})
"""
