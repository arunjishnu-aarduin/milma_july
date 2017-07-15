from .models import *
from django.contrib import messages
def getMethodPercentage(category,method):
    method_list=category.distinctMethodList
    method_percentage_list=MethodPercentage.objects.filter(category=category,method=method)

    #Method Percentage Validation
    # print "Method Count from Composition:"+str(method_list.count())
    # print "Method Count from MethodPercentage:",MethodPercentage.objects.filter(category=category).count()
    if (MethodPercentage.objects.filter(category=category).count()!=method_list.count()) and method_list.count()!=1:

        return 0

    if len(method_percentage_list) ==0:
        return 100
    else:
        return method_percentage_list[0].percentage


def requireIssue(category,sale_in_unit):
    #methodlist=Composition.objects.distinct().filter(cat_id_id=cat_id)
    print "Category:"+str(category)+"  sale in unit:"+str(sale_in_unit)

    method_list=Composition.objects.filter(category=category).values('method').distinct()

    global target_unit
    global target_inner


    target_method=0

    for method in method_list:
        #print "\t\tmethod"+method['method']
        composition_list=Category.objects.get(code=category.code).composition_set.filter(method=method['method'])
        target_composition=0
        print composition_list
        for composition in composition_list:
            print "\t\t"+composition.issue.name
            target_unit=0
            target_inner=0
            if composition.issue==requested_issue:
                # print "\t\t\tmatch     "+str(composition.issue)
                #changed to new method percentage function
                #target_unit+=composition.ratio*sale_in_unit*(composition.methodPercentage/100)



                target_unit+=composition.ratio*sale_in_unit*(getMethodPercentage(composition.category,composition.method)/100)



                print "\t\t\ttarget_unit",target_unit
            elif composition.issueType=='1':



                print "\t\t\ttype1"
                new_category=IssueAsCategory.objects.get(issue=composition.issue)
                new_sale_in_unit=sale_in_unit*composition.ratio
                print "\t\t\tnew_category "+new_category.category.name
                print "\t\t\tnew_sale_in_unit",new_sale_in_unit
                # print "category-----------------------------------------------------"+str(new_category.category)+"sale"+str(new_sale_in_unit)
                # continue
                target_inner+=requireIssue(new_category.category,new_sale_in_unit)
                print "\t\t\ttarget_inner",target_inner

            else :
                 print "\t\t\t\tnot match      "+str(composition.issue)

            # target_composition+=(target_unit+target_inner)
            target_composition+=target_unit



            # print "\t\t\t\tComposition_sum",target_composition
        target_method+=target_composition
    # print "target method                      "+str(target_method)
    return target_method


def totalIssueRequirement(month,diary,issue):
    CategoryList=Category.objects.all()
    month_issue_requirement=0
    for category in CategoryList:
        category_issue_requirement=0
        # print category
        global requested_issue




        saledetails=ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

        stockindetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

        stockoutdetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,from_diary=diary)

        salesum=0
        stockout=0
        stockin=0
        for sale in saledetails:

            # print "\t"+str(sale.product.code)+"-"+sale.product.category.name
            # print "\tsale in unit-"+str(sale.targetSalesUnit)
            # #salesum+=sale.targetSalesQuantity
            salesum+=sale.targetSalesUnit
        for stock in stockindetail:
            # print "\t"+str(stock.product.code)+"-"+stock.product.category.name
            # print "\tstockin in unit-"+str(stock.targetStockinUnit)
            # #stockin+=stock.targetStockinQuantity
            stockin+=stock.targetStockinUnit

        for stock in stockoutdetail:
            # print "\t"+str(stock.product.code)+"-"+stock.product.category.name
            # print "\tstockout in unit-"+str(stock.targetStockoutUnit)
            # #stockout+=stock.targetStockOutQuantity
            stockout+=stock.targetStockoutUnit

        # print "\tsales",salesum
        # print "\tstockout",stockout
        # print "\tstockin",stockin
        target=(salesum+stockout-(stockin))
        # print "\tRequired issue  "+issue.name
        requested_issue=issue
        # print "\tTarget",target



        #updated on14-07-2017

        category_issue_requirement+=requireIssue(category,target)
        month_issue_requirement+=category_issue_requirement

        print "category_issue_requirement returned :"+str(category_issue_requirement)
    #return { MONTHS[month]:month_issue_requirement}
    m,issueasproduct=IssueasProduct(month,diary,issue)
    month_issue_requirement+=issueasproduct
    return (MONTHS[month],month_issue_requirement)

def IssueasProduct(month,diary,issue):
    salesum=0
    stockout=0
    stockin=0
    try:
        issue_as_category=IssueAsCategory.objects.get(issue=issue)

        category=issue_as_category.category
        saledetails=ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

        stockindetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

        stockoutdetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,from_diary=diary)
        for sale in saledetails:


            #salesum+=sale.targetSalesQuantity
            salesum+=sale.targetSalesUnit

        for stock in stockindetail:


            #stockin+=stock.targetStockinQuantity

            stockin+=stock.targetStockinUnit
        for stock in stockoutdetail:

            #stockout+=stock.targetStockOutQuantity
            stockout+=stock.targetStockoutUnit

    except Exception as e:
        print "Exception handled for Issue As Category DoesNotExist"
        pass
    # messages.info(request, MONTHS[month]+"sale:"+str(salesum)+"stockout:"+str(stockout)+"stockin:"+str(stockin))



    target=(salesum+stockout-(stockin))
    print "\t\t\t\t\t\ttarget",str(target)
    # messages.info(request,"sale:"+str(salesum)+"stockout:"+str(stockout)+"stockin:"+str(stockin))
    print MONTHS[month]
    return (MONTHS[month],target)

def qcValue(milk_product):
    try:
        fc=Issue.objects.get(name='CREAM').fat
        fwm=Issue.objects.get(name='WM').fat
        mf=milk_product.fat

        qc=(fwm*((fc-fwm)/100)-(mf*(fc-fwm)))/((2*mf)-(fwm/100)-(fc/100))
        return qc
    except Exception as e:
        print "Exception handled from qcValue Function"
        return 0

def qwmValue(milk_product):
    try:
        fc=Issue.objects.get(name='CREAM').fat
        fwm=Issue.objects.get(name='WM').fat
        qc=qcValue(milk_product)
        qwm=fc-fwm+qc
        return qwm
    except Exception as e:
         print "Exception handled from qwmValue Function"
         return 0

def kValue(milk_product):
    try:
        qc=qcValue(milk_product)
        qwm=qwmValue(milk_product)
        swm=Issue.objects.get(name='WM').snf
        sc=Issue.objects.get(name='CREAM').snf
        k=(((qwm/100)*swm)+((qc/100)*sc))/(qwm+qc)
        return k
    except Exception as e:
        print "Exception handled from kValue Function"
        return 0

def qsmpValue(milk_product):
    try:
        qwm=qwmValue(milk_product)
        qc=qcValue(milk_product)
        sm=milk_product.snf
        ssmp=Issue.objects.get(name='SMP').snf
        k=kValue(milk_product)
        qsmp=(qwm+qc)*((sm-k)/(ssmp-sm))
        return qsmp
    except Exception as e:
        print "Exception handled from qsmpValue Function"
        return 0
