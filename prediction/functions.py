from .models import *
from django.contrib import messages
import timeit

#functions start here

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


def requireIssue(category,sale_in_unit,categoryList):
	#methodlist=Composition.objects.distinct().filter(cat_id_id=cat_id)
	# print "Category:"+str(category)+"  sale in unit:"+str(sale_in_unit)

	method_list=Composition.objects.filter(category=category).values('method').distinct()



	global target_unit
	global target_inner


	target_method=0

	for method in method_list:
		#print "\t\tmethod"+method['method']
		composition_list=Category.objects.get(code=category.code).composition_set.filter(method=method['method'])
		target_composition=0
		# print composition_list
		for composition in composition_list:
			# print "\t\t"+composition.issue.name
			target_unit=0
			target_inner=0
			if composition.issue==requested_issue:
				# print "\t\t\tmatch     "+str(composition.issue)
				#changed to new method percentage function
				#target_unit+=composition.ratio*sale_in_unit*(composition.methodPercentage/100)



				target_unit+=composition.ratio*sale_in_unit*(getMethodPercentage(composition.category,composition.method)/100)



				# print "\t\t\ttarget_unit",target_unit
			elif composition.issueType=='1':



				# print "\t\t\ttype1"
				try:
					new_category=IssueAsCategory.objects.get(issue=composition.issue)
					if new_category in categoryList:

						new_sale_in_unit=sale_in_unit*composition.ratio
				# print "\t\t\tnew_category "+new_category.category.name
				# print "\t\t\tnew_sale_in_unit",new_sale_in_unit
				# print "category-----------------------------------------------------"+str(new_category.category)+"sale"+str(new_sale_in_unit)
				# continue
						target_inner+=requireIssue(new_category.category,new_sale_in_unit,categoryList)
				except Exception as e:
					print "Exception handled for Issue As Category DoesNotExist{Require Issue Function}"
					pass
				# print "\t\t\ttarget_inner",target_inner

			# else :
			# 	 print "\t\t\t\tnot match      "+str(composition.issue)

			# target_composition+=(target_unit+target_inner)
			target_composition+=target_unit



			# print "\t\t\t\tComposition_sum",target_composition
		target_method+=target_composition
	# print "target method                      "+str(target_method)
	return target_method


def totalIssueRequirement(month,diary,issue):


	# CategoryList=Category.objects.all()
	#Only Category List Changed on 27-07-2017
	CategoryListFromComposition=Composition.objects.filter(issue=issue)



	IssueUsedAsCategoryIndirectList=IssueUsedAsCategoryIndirect.objects.filter(issue=issue)
	categoryList=[]

	for item in CategoryListFromComposition:
		if item.category not in  categoryList:
			categoryList.append(item.category)
	for item in IssueUsedAsCategoryIndirectList:
		if item.category not in categoryList:
			categoryList.append(item.category)


	# print "category list direct + indirect ----",categoryList

	month_issue_requirement=0
	#--Changes End here
	# start = timeit.default_timer()
	for category in categoryList:

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

		category_issue_requirement+=requireIssue(category,target,categoryList)

		month_issue_requirement+=category_issue_requirement



		# print str(category.name)+"category_issue_requirement returned :"+str(month_issue_requirement)+"-"+str(MONTHS[month])
	#return { MONTHS[month]:month_issue_requirement}



	m,issueasproduct=IssueasProduct(month,diary,issue)
	# print "Issue as Product target sale-"+str(issueasproduct)
	month_issue_requirement+=issueasproduct
	# stop = timeit.default_timer()
    #
	# print str(month) + "-" + str(diary.name) + " Time-------------------" + str(issue.name) + "  " + str(stop - start)



	return (MONTHS[month],month_issue_requirement)
def totalIssueRequirementDB(diary,month,category):


	start = timeit.default_timer()
	Issue_List=Issue.objects.all()
	for issue in Issue_List:


		month_issue_requirement=0

		category_issue_requirement=0

		global requested_issue

		saledetails=ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

		stockindetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,diary=diary)

		stockoutdetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month,from_diary=diary)

		salesum=0
		stockout=0
		stockin=0
		for sale in saledetails:
			salesum+=sale.targetSalesUnit
		for stock in stockindetail:
			stockin+=stock.targetStockinUnit

		for stock in stockoutdetail:
			stockout+=stock.targetStockoutUnit

		target=(salesum+stockout-(stockin))
		requested_issue=issue



		#updated on14-07-2017

		category_issue_requirement+=requireIssue(category,target)
		month_issue_requirement+=category_issue_requirement



		m,issueasproduct=IssueasProduct(month,diary,issue)
		month_issue_requirement+=issueasproduct
		# print  "month issue"+str(month_issue_requirement)
		obj, created = IssueRequirement.objects.update_or_create(
				diary=diary, month=month, issue=issue,
				defaults={'requirement': month_issue_requirement},

			)
	stop = timeit.default_timer()

	print str(diary.name) + "Time-------------------" + str(stop - start)




def issueRequirementDB(diary,month,issue):

	IssueList=Composition.objects.filter(issue=issue)

	for item in IssueList:
		totalIssueRequirementDB(diary,month,item.category)




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
		print "Exception handled for Issue As Category DoesNotExist Issue:"+str(issue)
		pass
	# messages.info(request, MONTHS[month]+"sale:"+str(salesum)+"stockout:"+str(stockout)+"stockin:"+str(stockin))



	target=(salesum+stockout-(stockin))
	# print "\t\t\t\t\t\ttarget",str(target)
	# messages.info(request,"sale:"+str(salesum)+"stockout:"+str(stockout)+"stockin:"+str(stockin))
	# print MONTHS[month]
	return (MONTHS[month],target)

def qcValue(milk_product):
	try:
		fc=Issue.objects.get(name='CREAM').fat
		sc = Issue.objects.get(name='CREAM').snf
		fwm=Issue.objects.get(name='WM').fat
		swm=Issue.objects.get(name='WM').snf
		mf=milk_product.fat
		ms = milk_product.snf
		qwm=qwmValue(milk_product)
		qsmp=qsmpValue(milk_product)
		fsmp = Issue.objects.get(name='SMP').fat
		ssmp = Issue.objects.get(name='SMP').snf


		if (mf>fwm):
			qc=-1*(((qwm*(mf-fwm))/(mf-fc))+((qsmp*(mf-fsmp))/(mf-fc)))

		else:
			qc=((qwm*(ms-swm))/(ms-sc))+((qsmp*(ms-ssmp))/(ms-sc))

		return qc
	except Exception as e:
		print "Exception handled from qcValue Function"
		return 0

def qwmValue(milk_product):
	try:
		fc=Issue.objects.get(name='CREAM').fat
		fwm=Issue.objects.get(name='WM').fat


		qwm=fc-fwm
		return qwm
	except Exception as e:
		 print "Exception handled from qwmValue Function"
		 return 0



def qsmpValue(milk_product):
	try:
		qwm=qwmValue(milk_product)

		ms=milk_product.snf
		swm = Issue.objects.get(name='WM').snf
		ssmp=Issue.objects.get(name='SMP').snf
		fsmp=Issue.objects.get(name='SMP').fat
		sc=Issue.objects.get(name='CREAM').snf
		fc = Issue.objects.get(name='CREAM').fat
		mf = milk_product.fat
		fwm = Issue.objects.get(name='WM').fat






		qsmp=qwm*((((ms-swm)*(mf-fc))-((ms-sc)*(mf-fwm)))/(((mf-fsmp)*(ms-sc))-((ms-ssmp)*(mf-fc))))

		return qsmp
	except Exception as e:
		print "Exception handled from qsmpValue Function"
		return 0


def qcReconstitutionValueSmp():
	try:
		fc=Issue.objects.get(name='CREAM').fat
		fwm=Issue.objects.get(name='WM').fat

		qc=(fwm/fc)*100
		return qc
	except Exception as e:
		print "Exception handled from qcValueReconstitution Function"
		return 0
def kReconstitutionValueSmp():
	try:
		sc = Issue.objects.get(name='CREAM').snf

		k=qcReconstitutionValueSmp()*sc/100
		return k
	except Exception as e:
		print "Exception handled from kValueReconstitution Function"
		return 0

def qsmpReconstitutionValueSmp():
	try:
		swm = Issue.objects.get(name='WM').snf
		ssmp = Issue.objects.get(name='SMP').snf
		qsmp=((swm-kReconstitutionValueSmp())/ssmp)*100
		return qsmp
	except Exception as e:
		print "Exception handled from qsmpValueReconstitution Function"
		return 0

def qwmValueCSM():
	try:
		fc = Issue.objects.get(name='CREAM').fat
		fwm = Issue.objects.get(name='WM').fat
		qwm=fc-fwm

		return qwm
	except Exception as e:
		print "Exception handled from qwmValueReconstitution(CSM) Function"
		return 0
def qcValueCSM():
	try:
		qwm=qwmValueCSM()
		fc = Issue.objects.get(name='CREAM').fat
		fwm = Issue.objects.get(name='WM').fat
		fcsm=GeneralCalculation.objects.get(code=17).value
		qc=(qwm*(fwm-fcsm))/(fc-fcsm)

		return qc

	except Exception as e:
		print "Exception handled from qcValueReconstitution(CSM) Function"
		return 0

def qsmpReconstitutionValueWMP():
	try:

		qw=GeneralCalculation.objects.get(code=18).value
		fwmp=qw
		swm=Issue.objects.get(name='WM').snf
		swmp=GeneralCalculation.objects.get(code=19).value
		fwm=Issue.objects.get(name='WM').fat
		fsmp=Issue.objects.get(name='SMP').fat
		ssmp=Issue.objects.get(name='SMP').snf

		qsmp=qw*(((fwm*(swm-swmp))-(swm*(fwm-fwmp)))/(((fwm-fsmp)*(swm-swmp))-((fwm-fwmp)*(swm-ssmp))))

		return qsmp
	except Exception as e:
		print "Exception Handled At qsmpReconstitutionValueWMP"
		return 0
def qwmpReconstitutionValueWMP():
	try:
		qsmp=qsmpReconstitutionValueWMP()
		fwm = Issue.objects.get(name='WM').fat
		fsmp = Issue.objects.get(name='SMP').fat
		qw = GeneralCalculation.objects.get(code=18).value
		fwmp = qw

		qwmp=((qsmp*(fwm-fsmp))-(qw*fwm))/(fwm-fwmp)
		return qwmp

	except Exception as e:
		print "Exception Handled at qwmpReconstitutionValueWMP"
		return  0





def scsmCalculation():
	try:
		qwm=qwmValueCSM()
		swm=Issue.objects.get(name='WM').snf
		qc=qcValueCSM()
		sc=Issue.objects.get(name='CREAM').snf

		scsm=((qwm*swm)-(qc*sc))/(qwm-qc)



		return  scsm

	except Exception as e:
		print "Exception handled from scsmCalculation"
		return 0

def psmpCalculation(pcsm):

	try:
		snf_yield=GeneralCalculation.objects.get(code=20).value
		scsm=scsmCalculation()
		ssmp = Issue.objects.get(name='SMP').snf



		psmp=(pcsm*(scsm/100)*(snf_yield/100))/(ssmp/100)

		return psmp
	except Exception as e:
		print "Exception Handled At psmpCalculation"
		return 0



def interMilkTransfer(shortage_list,surplus_list,total_requirement_diary_cpd,diaryList):
	resultitem = []

	if total_requirement_diary_cpd>0:

		if "KOZHIKODE" in surplus_list.keys():

			if total_requirement_diary_cpd > surplus_list["KOZHIKODE"]:
				surplus_difference = total_requirement_diary_cpd - surplus_list["KOZHIKODE"]

				del surplus_list["KOZHIKODE"]
				shortage_list["KOZHIKODE"] = surplus_difference
			else:
				surplus_list["KOZHIKODE"] -= total_requirement_diary_cpd

			if "CENTRAL PRODUCTS" in shortage_list.keys():
				del shortage_list["CENTRAL PRODUCTS"]
		elif "KOZHIKODE" in shortage_list.keys():

			# shortage_list["KOZHIKODE"] -= total_requirement_diary_cpd

			shortage_list["KOZHIKODE"] += total_requirement_diary_cpd


			shortage_list["KOZHIKODE"] = shortage_list["KOZHIKODE"]

			if shortage_list["KOZHIKODE"]<0:
				shortage_list["KOZHIKODE"]=shortage_list["KOZHIKODE"]*(-1)
			if "CENTRAL PRODUCTS" in shortage_list.keys():
				del shortage_list["CENTRAL PRODUCTS"]


		result = {"fromdiary": "KOZHIKODE", "todiary": "CENTRAL PRODUCTS", "value": total_requirement_diary_cpd}
		resultitem.append(result)


	inter_stock_transfer_list=InterStockMilkTransferOrder.objects.all()

	# print str(shortage_list)
	# print str(surplus_list)


	for item in inter_stock_transfer_list:
		from_diary= str(item.from_diary.name)
		to_diary=str(item.to_diary.name)
		if item.priority!=1:
			if from_diary in surplus_list.keys() and to_diary in shortage_list.keys():
				if surplus_list[from_diary]> shortage_list[to_diary]:
					difference=surplus_list[from_diary]-shortage_list[to_diary]

					result = {"fromdiary":from_diary,"todiary":to_diary,"value":shortage_list[to_diary]}
					surplus_list[from_diary] = difference
					del shortage_list[to_diary]
					# print str(surplus_list)
					# print str(shortage_list)
				else:



					difference=shortage_list[to_diary]-surplus_list[from_diary]


					result = {"fromdiary": from_diary, "todiary": to_diary, "value": surplus_list[from_diary]}
					shortage_list[to_diary] = difference

					del surplus_list[from_diary]


				resultitem.append(result)




	value_after_stock_transfer=0
	surplus_value=0
	shortage_value=0

	# print "surplus"
	# print surplus_list
	# print "shortage"
	# print shortage_list

	diary_after_stock_transfer=[]
	if bool(surplus_list):

		for item,value in surplus_list.items():
			result={'diary':item,'value':value,'type':"Surplus"}
			diary_after_stock_transfer.append(result)
			# if current_diary.name==item:
			# 	surplus_value +=value



	if bool(shortage_list):
		for item, value in shortage_list.items():
			result = {'diary': item, 'value': value,'type':"Shortage"}
			diary_after_stock_transfer.append(result)
			# if current_diary.name == item:
			# 	shortage_value += value


	# value_after_stock_transfer=surplus_value-shortage_value



	stock_transfer=[]
	for diary in diaryList:




		for item in resultitem:
			if diary.name==item['fromdiary'] or diary.name==item['todiary']:
				if item['fromdiary']==diary.name:
					transfer_type="to"
					to_or_from_diary=item['todiary']

				elif item['todiary']==diary.name:
					transfer_type="from"
					to_or_from_diary=item['fromdiary']

				result={"diary":diary.name,"type":transfer_type,"to_or_from_diary":to_or_from_diary,"value":item['value']}
				stock_transfer.append((result))




	# print stock_transfer

	return diary_after_stock_transfer,stock_transfer

def wmBalancing(after_transfer_diary_list,month):
	wm_balanced_diarylist=[]
	for item in after_transfer_diary_list:


		after_transfer_value = item['value']
		wm_after_stock_transfer=[]

		wmp_total_wmp_reconstitution=0
		smp_total_smp_reconstitution=0
		smp_total_wmp_reconstitution=0
		csm_converted_to_smp=0
		cream_total_csm=0
		cream_total_smp_reconstitution=0
		wm_total_csm=0
		water_total_wmp_reconstitution=0
		water_total_smp_reconstitution=0

		if item['type'] =="Shortage":

			procurement_of_month = 0
			try:
				diary=Diary.objects.get(name=item['diary'])
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)
				procurement_of_month = Awm_obj.targetProcurement
			except Exception as e:
				print "Exception handled wmBalancing in line 640"

			max_allowable_reconstitution = procurement_of_month * GeneralCalculation.objects.get(code=1).value / 100



			reconstitution_amount = 0



			if max_allowable_reconstitution < after_transfer_value:
				wm_purchase = after_transfer_value - max_allowable_reconstitution
				purchase_rate = GeneralCalculation.objects.get(code=8).value


				reconstitution_amount = max_allowable_reconstitution
			else:
				reconstitution_amount = max_allowable_reconstitution - after_transfer_value

			if reconstitution_amount != 0:

				transaction_item = {
					'transaction': "WM Reconstituted:" + str(reconstitution_amount)}
				wm_after_stock_transfer.append(transaction_item)




				reconstitution_from_smp = reconstitution_amount * GeneralCalculation.objects.get(code=2).value / 100
				try:

					quantity_of_water = 100 - qcReconstitutionValueSmp() - qsmpReconstitutionValueSmp()
					cream_ratio = qcReconstitutionValueSmp() / 100
					smp_ratio = qsmpReconstitutionValueSmp() / 100
					water_ratio = quantity_of_water / 100

					smp_total_smp_reconstitution = reconstitution_from_smp * smp_ratio
					cream_total_smp_reconstitution = reconstitution_from_smp * cream_ratio
					water_total_smp_reconstitution = reconstitution_from_smp * water_ratio

					transaction_item={'transaction':" WM Reconstituted From SMP:"+str(reconstitution_from_smp)}

					wm_after_stock_transfer.append(transaction_item)
				except Exception as e:
					print  "Exception Handled wmBalancing At 678 "

				reconstitution_from_wmp = reconstitution_amount * GeneralCalculation.objects.get(code=3).value / 100

				try:

					qw = GeneralCalculation.objects.get(code=18).value

					water_ratio_wmp=qw/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					wmp_ratio_wmp=qwmpReconstitutionValueWMP()/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					smp_ratio_wmp=(-1*qsmpReconstitutionValueWMP())/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())

					water_total_wmp_reconstitution=reconstitution_from_wmp*water_ratio_wmp
					wmp_total_wmp_reconstitution=reconstitution_from_wmp*wmp_ratio_wmp
					smp_total_wmp_reconstitution=reconstitution_from_wmp*smp_ratio_wmp
				except Exception as e:
					print "Exception Handled  wmBalancing At 695 "


				transaction_item={'transaction':" WM Reconstituted From WMP:" + str(
					reconstitution_from_wmp)}
				wm_after_stock_transfer.append(transaction_item)

				transaction_item = {'transaction': " Water for Reconstitution From SMP:" + str(
					water_total_smp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)

				transaction_item = {'transaction': " Cream for Reconstitution From SMP:" + str(
					cream_total_smp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)

				transaction_item = {'transaction': " SMP for Reconstitution From SMP:" + str(
					smp_total_smp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)
				transaction_item = {'transaction': " Water for Reconstitution From WMP:" + str(
					water_total_wmp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)

				transaction_item = {'transaction': " WMP for Reconstitution From WMP:" + str(
					wmp_total_wmp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)

				transaction_item = {'transaction': " SMP Obtained in Reconstitution From WMP:" + str(
					smp_total_wmp_reconstitution)}
				wm_after_stock_transfer.append(transaction_item)



				transaction_item = {
					'transaction': "WM Purchased:" + str(wm_purchase) + ", Amount:" + str(
						wm_purchase * purchase_rate)}
				wm_after_stock_transfer.append(transaction_item)


		else:


			sale_percentage = GeneralCalculation.objects.get(code=4).value
			sale_rate = GeneralCalculation.objects.get(code=9).value

			wm_for_sale = after_transfer_value * sale_percentage / 100



			transaction_item = {'transaction': " WM Sold:" + str(wm_for_sale) + ", Amount:" + str(
				wm_for_sale * sale_rate)}

			wm_after_stock_transfer.append(transaction_item)


			csm_convert_percentage = GeneralCalculation.objects.get(code=5).value
			wm_converted_to_csm = after_transfer_value * csm_convert_percentage / 100



			transaction_item = {'transaction': " WM Converted to CSM:" + str(wm_converted_to_csm)}
			wm_after_stock_transfer.append(transaction_item)


			csm_wm_ratio = qwmValueCSM() / (qwmValueCSM() - qcValueCSM())
			csm_cream_ratio = -1 * (
			qcValueCSM() / (qwmValueCSM() - qcValueCSM()))



			scsm = scsmCalculation()
			csm_smp_conversion_percentage = GeneralCalculation.objects.get(code=7).value
			# pwm_for_conversion = wm_converted_to_csm * csm_smp_conversion_percentage / 100
			pcsm_for_conversion=wm_converted_to_csm/csm_wm_ratio

			# wm_total_csm = wm_converted_to_csm * csm_wm_ratio
			# cream_total_csm = wm_converted_to_csm * csm_cream_ratio
			wm_total_csm = wm_converted_to_csm
			cream_total_csm=pcsm_for_conversion*csm_cream_ratio



			csm_sale_percentage = GeneralCalculation.objects.get(code=6).value
			csm_sale_rate = GeneralCalculation.objects.get(code=10).value
			csm_sold = pcsm_for_conversion * csm_sale_percentage / 100
			csm_sold_amount = csm_sold * csm_sale_rate



			transaction_item = {
				'transaction': " Quantity of CSM Obtained:" + str(pcsm_for_conversion)}
			wm_after_stock_transfer.append(transaction_item)



			transaction_item = {
				'transaction': " Quantity of Cream Obtained in CSM Conversion:" + str(pcsm_for_conversion * csm_cream_ratio)}


			wm_after_stock_transfer.append(transaction_item)



			transaction_item = {'transaction': " SNF Percentage of CSM:" + str(scsm)}

			wm_after_stock_transfer.append(transaction_item)



			transaction_item = {'transaction': " CSM Sold:" + str(csm_sold) + ", Amount:" +str(csm_sold_amount)}

			wm_after_stock_transfer.append(transaction_item)




			csm_converted_to_smp_display=pcsm_for_conversion*(csm_smp_conversion_percentage/100)

			csm_converted_to_smp = psmpCalculation(csm_converted_to_smp_display)



			transaction_item = {
				'transaction': " CSM Converted to SMP:" + str(csm_converted_to_smp_display)}
			wm_after_stock_transfer.append(transaction_item)



			transaction_item = {
				'transaction': " Quantity of SMP Obtained from CSM:" + str(csm_converted_to_smp)}
			wm_after_stock_transfer.append(transaction_item)



		resultitem={'diary':item['diary'],'after_transfer':str(item['type'])+" : "+str(item['value']),'transactions':wm_after_stock_transfer,'wmp_used':wmp_total_wmp_reconstitution
			,'smp_used_smp':smp_total_smp_reconstitution,'smp_used_wmp':smp_total_wmp_reconstitution,'converted_smp':csm_converted_to_smp,'cream_used_csm':cream_total_csm
					,'cream_used_smp':cream_total_smp_reconstitution,'wm_used_csm':wm_total_csm,'water_used_wmp':water_total_wmp_reconstitution
					,'water_used_smp':water_total_smp_reconstitution}
		wm_balanced_diarylist.append(resultitem)




	return wm_balanced_diarylist

def wmBalancingReportFinance(after_transfer_diary_list,month):
	wm_balanced_diarylist=[]
	wm_purchase_list=[]
	for item in after_transfer_diary_list:


		after_transfer_value = item['value']
		wm_after_stock_transfer=[]

		wmp_total_wmp_reconstitution=0
		smp_total_smp_reconstitution=0
		smp_total_wmp_reconstitution=0
		csm_converted_to_smp=0
		cream_total_csm=0
		cream_total_smp_reconstitution=0
		wm_total_csm=0
		water_total_wmp_reconstitution=0
		water_total_smp_reconstitution=0
		wm_purchase_amount=0
		if item['type'] =="Shortage":

			procurement_of_month = 0
			try:
				diary=Diary.objects.get(name=item['diary'])
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)
				procurement_of_month = Awm_obj.targetProcurement
			except Exception as e:
				print "Exception handled wmBalancing in line 640"

			max_allowable_reconstitution = procurement_of_month * GeneralCalculation.objects.get(code=1).value / 100



			reconstitution_amount = 0



			if max_allowable_reconstitution < after_transfer_value:
				wm_purchase = after_transfer_value - max_allowable_reconstitution
				purchase_rate = GeneralCalculation.objects.get(code=8).value
				wm_purchase_amount=wm_purchase * purchase_rate
				transaction_item={'transaction':"WM Purchased:" + str(wm_purchase) + ", Amount:" + str(
					wm_purchase_amount)}
				wm_after_stock_transfer.append(transaction_item)

				reconstitution_amount = max_allowable_reconstitution
			else:
				reconstitution_amount = max_allowable_reconstitution - after_transfer_value

			if reconstitution_amount != 0:

				reconstitution_from_smp = reconstitution_amount * GeneralCalculation.objects.get(code=2).value / 100
				try:

					quantity_of_water = 100 - qcReconstitutionValueSmp() - qsmpReconstitutionValueSmp()
					cream_ratio = qcReconstitutionValueSmp() / 100
					smp_ratio = qsmpReconstitutionValueSmp() / 100
					water_ratio = quantity_of_water / 100

					smp_total_smp_reconstitution = reconstitution_from_smp * smp_ratio
					cream_total_smp_reconstitution = reconstitution_from_smp * cream_ratio
					water_total_smp_reconstitution = reconstitution_from_smp * water_ratio

					transaction_item={'transaction':" WM Reconstituted From SMP:"+str(reconstitution_from_smp)}

					wm_after_stock_transfer.append(transaction_item)
				except Exception as e:
					print  "Exception Handled wmBalancing At 678 "

				reconstitution_from_wmp = reconstitution_amount * GeneralCalculation.objects.get(code=3).value / 100

				try:

					qw = GeneralCalculation.objects.get(code=18).value

					water_ratio_wmp=qw/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					wmp_ratio_wmp=qwmpReconstitutionValueWMP()/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					smp_ratio_wmp=(-1*qsmpReconstitutionValueWMP())/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())

					water_total_wmp_reconstitution=reconstitution_from_wmp*water_ratio_wmp
					wmp_total_wmp_reconstitution=reconstitution_from_wmp*wmp_ratio_wmp
					smp_total_wmp_reconstitution=reconstitution_from_wmp*smp_ratio_wmp
				except Exception as e:
					print "Exception Handled  wmBalancing At 695 "


				transaction_item={'transaction':" WM Reconstituted From WMP:" + str(
					reconstitution_from_wmp)}
				wm_after_stock_transfer.append(transaction_item)


		else:


			sale_percentage = GeneralCalculation.objects.get(code=4).value
			sale_rate = GeneralCalculation.objects.get(code=9).value

			wm_for_sale = after_transfer_value * sale_percentage / 100

			transaction_item={'transaction':" WM Sold:" + str(wm_for_sale) + ", Amount:" + str(
				wm_for_sale * sale_rate)}

			wm_after_stock_transfer.append(transaction_item)


			csm_convert_percentage = GeneralCalculation.objects.get(code=5).value
			wm_converted_to_csm = after_transfer_value * csm_convert_percentage / 100

			transaction_item={'transaction':" WM Converted to CSM:"+str(wm_converted_to_csm)}
			wm_after_stock_transfer.append(transaction_item)


			csm_wm_ratio = qwmValueCSM() / (qwmValueCSM() - qcValueCSM())
			csm_cream_ratio = -1 * (
			qcValueCSM() / (qwmValueCSM() - qcValueCSM()))


			csm_smp_conversion_percentage = GeneralCalculation.objects.get(code=7).value
			pcsm_for_conversion = wm_converted_to_csm / csm_wm_ratio

			wm_total_csm = wm_converted_to_csm
			cream_total_csm =  pcsm_for_conversion * csm_cream_ratio


			scsm = scsmCalculation()

			transaction_item={'transaction':" SNF Percentage of CSM:" + str(scsm)}

			wm_after_stock_transfer.append(transaction_item)

			csm_sale_percentage = GeneralCalculation.objects.get(code=6).value
			csm_sale_rate = GeneralCalculation.objects.get(code=10).value
			csm_sold = pcsm_for_conversion * csm_sale_percentage / 100

			csm_sold_amount = csm_sold * csm_sale_rate


			transaction_item={'transaction':" CSM Sold:" + str(csm_sold) + ", Amount:" + str(
				csm_sold_amount)}
			wm_after_stock_transfer.append(transaction_item)

			csm_converted_to_smp_display = pcsm_for_conversion * (csm_smp_conversion_percentage / 100)


			csm_converted_to_smp =psmpCalculation(csm_converted_to_smp_display)

			transaction_item={'transaction':" CSM Converted to SMP:" + str(csm_converted_to_smp_display)}
			wm_after_stock_transfer.append(transaction_item)



		resultitem={'diary':item['diary'],'after_transfer':str(item['type'])+" : "+str(item['value']),'transactions':wm_after_stock_transfer,'wmp_used':wmp_total_wmp_reconstitution
			,'smp_used_smp':smp_total_smp_reconstitution,'smp_used_wmp':smp_total_wmp_reconstitution,'converted_smp':csm_converted_to_smp,'cream_used_csm':cream_total_csm
					,'cream_used_smp':cream_total_smp_reconstitution,'wm_used_csm':wm_total_csm,'water_used_wmp':water_total_wmp_reconstitution
					,'water_used_smp':water_total_smp_reconstitution}
		wm_balanced_diarylist.append(resultitem)


		purchase_item={'diary':item['diary'],'Amount':wm_purchase_amount}
		wm_purchase_list.append(purchase_item)




	return wm_balanced_diarylist,wm_purchase_list


def wmBalancingReport(after_transfer_diary_list,month):
	wm_balanced_diarylist=[]
	wm_reconstitution_union=0
	wm_purchase_union=0
	wm_sale_union=0
	csm_sale_union=0
	cream_reconstitution_union=0
	smp_from_conversion=0
	reconstitution_amount=0
	csm_converted_to_smp=0
	for item in after_transfer_diary_list:


		after_transfer_value = item['value']
		wm_after_stock_transfer=[]

		wmp_total_wmp_reconstitution=0
		smp_total_smp_reconstitution=0
		smp_total_wmp_reconstitution=0
		csm_converted_to_smp=0
		cream_total_csm=0
		cream_total_smp_reconstitution=0
		wm_total_csm=0
		water_total_wmp_reconstitution=0
		water_total_smp_reconstitution=0

		if item['type'] =="Shortage":

			procurement_of_month = 0
			try:
				diary=Diary.objects.get(name=item['diary'])
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)
				procurement_of_month = Awm_obj.targetProcurement
			except Exception as e:
				print "Exception handled wmBalancingReport in line 804"

			max_allowable_reconstitution = procurement_of_month * GeneralCalculation.objects.get(code=1).value / 100



			reconstitution_amount = 0



			if max_allowable_reconstitution < after_transfer_value:
				wm_purchase = after_transfer_value - max_allowable_reconstitution
				purchase_rate = GeneralCalculation.objects.get(code=8).value
				transaction_item={'transaction':"WM Purchased:" + str(wm_purchase) + ", Amount:" + str(
					wm_purchase * purchase_rate)}
				wm_after_stock_transfer.append(transaction_item)

				wm_purchase_union+=wm_purchase

				reconstitution_amount = max_allowable_reconstitution
			else:
				reconstitution_amount = max_allowable_reconstitution - after_transfer_value

			if reconstitution_amount != 0:

				reconstitution_from_smp = reconstitution_amount * GeneralCalculation.objects.get(code=2).value / 100
				try:

					quantity_of_water = 100 - qcReconstitutionValueSmp() - qsmpReconstitutionValueSmp()
					cream_ratio = qcReconstitutionValueSmp() / 100
					smp_ratio = qsmpReconstitutionValueSmp() / 100
					water_ratio = quantity_of_water / 100

					smp_total_smp_reconstitution = reconstitution_from_smp * smp_ratio
					cream_total_smp_reconstitution = reconstitution_from_smp * cream_ratio
					water_total_smp_reconstitution = reconstitution_from_smp * water_ratio

					transaction_item={'transaction':" WM Reconstituted From SMP:"+str(reconstitution_from_smp)}

					wm_after_stock_transfer.append(transaction_item)
				except Exception as e:
					print  "Exception Handled wmBalancingReport At 845 "

				reconstitution_from_wmp = reconstitution_amount * GeneralCalculation.objects.get(code=3).value / 100

				try:

					qw = GeneralCalculation.objects.get(code=18).value

					water_ratio_wmp=qw/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					wmp_ratio_wmp=qwmpReconstitutionValueWMP()/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					smp_ratio_wmp=(-1*qsmpReconstitutionValueWMP())/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())

					water_total_wmp_reconstitution=reconstitution_from_wmp*water_ratio_wmp
					wmp_total_wmp_reconstitution=reconstitution_from_wmp*wmp_ratio_wmp
					smp_total_wmp_reconstitution=reconstitution_from_wmp*smp_ratio_wmp
				except Exception as e:
					print "Exception Handled wmBalancingReport At  861 "


				transaction_item={'transaction':" WM Reconstituted From WMP:" + str(
					reconstitution_from_wmp)}
				wm_after_stock_transfer.append(transaction_item)


		else:


			sale_percentage = GeneralCalculation.objects.get(code=4).value
			sale_rate = GeneralCalculation.objects.get(code=9).value

			wm_for_sale = after_transfer_value * sale_percentage / 100

			transaction_item={'transaction':" WM Sold:" + str(wm_for_sale) + ", Amount:" + str(
				wm_for_sale * sale_rate)}

			wm_sale_union+=wm_for_sale

			wm_after_stock_transfer.append(transaction_item)


			csm_convert_percentage = GeneralCalculation.objects.get(code=5).value
			wm_converted_to_csm = after_transfer_value * csm_convert_percentage / 100

			transaction_item={'transaction':" WM Converted to CSM:"+str(wm_converted_to_csm)}
			wm_after_stock_transfer.append(transaction_item)


			csm_wm_ratio = qwmValueCSM() / (qwmValueCSM() - qcValueCSM())
			csm_cream_ratio = -1 * (
			qcValueCSM() / (qwmValueCSM() - qcValueCSM()))

			csm_smp_conversion_percentage = GeneralCalculation.objects.get(code=7).value

			pcsm_for_conversion = wm_converted_to_csm / csm_wm_ratio



			wm_total_csm = wm_converted_to_csm
			cream_total_csm = pcsm_for_conversion * csm_cream_ratio

			scsm = scsmCalculation()



			transaction_item={'transaction':" SNF Percentage of CSM:" + str(scsm)}

			wm_after_stock_transfer.append(transaction_item)

			csm_sale_percentage = GeneralCalculation.objects.get(code=6).value
			csm_sale_rate = GeneralCalculation.objects.get(code=10).value
			csm_sold = pcsm_for_conversion * csm_sale_percentage / 100
			csm_sold_amount = csm_sold * csm_sale_rate

			csm_sale_union+=csm_sold

			transaction_item={'transaction':" CSM Sold:" + str(csm_sold) + ", Amount:" + str(
				csm_sold_amount)}
			wm_after_stock_transfer.append(transaction_item)

			csm_converted_to_smp_display = pcsm_for_conversion * (csm_smp_conversion_percentage / 100)

			csm_converted_to_smp =psmpCalculation(csm_converted_to_smp_display)
			smp_from_conversion += csm_converted_to_smp

			transaction_item={'transaction':" CSM Converted to SMP:" + str(csm_converted_to_smp_display)}
			wm_after_stock_transfer.append(transaction_item)

		wm_reconstitution_union+=reconstitution_amount
		cream_reconstitution_union+=cream_total_smp_reconstitution



		resultitem={'diary':item['diary'],'after_transfer':str(item['type'])+" : "+str(item['value']),'transactions':wm_after_stock_transfer,'wmp_used':wmp_total_wmp_reconstitution
			,'smp_used_smp':smp_total_smp_reconstitution,'smp_used_wmp':smp_total_wmp_reconstitution,'converted_smp':csm_converted_to_smp,'cream_used_csm':cream_total_csm
					,'cream_used_smp':cream_total_smp_reconstitution,'wm_used_csm':wm_total_csm,'water_used_wmp':water_total_wmp_reconstitution
					,'water_used_smp':water_total_smp_reconstitution}
		wm_balanced_diarylist.append(resultitem)




	return wm_balanced_diarylist,wm_reconstitution_union,wm_purchase_union,wm_sale_union,csm_sale_union,smp_from_conversion,cream_reconstitution_union,smp_from_conversion

def wmBalancingReportDiaryWise(after_transfer_diary_list,month,current_diary):
	wm_balanced_diarylist=[]
	wm_reconstitution_union=0
	wm_purchase_union=0
	wm_sale_union=0
	csm_sale_union=0
	cream_reconstitution_union=0

	smp_rc_smp_union=0
	smp_rc_wmp_union=0
	water_rc_smp_union=0
	water_rc_wmp_union=0
	wmp_rc_wmp_union=0

	smp_from_conversion=0
	reconstitution_amount=0
	csm_converted_to_smp=0
	wm_for_csm=0
	cream_for_csm=0
	smp_from_conversion_union=0
	wm_converted_to_csm_union=0
	csm_for_conversion=0
	for item in after_transfer_diary_list:


		after_transfer_value = item['value']
		wm_after_stock_transfer=[]

		wmp_total_wmp_reconstitution=0
		smp_total_smp_reconstitution=0
		smp_total_wmp_reconstitution=0
		csm_converted_to_smp=0
		cream_total_csm=0
		cream_total_smp_reconstitution=0
		wm_total_csm=0
		water_total_wmp_reconstitution=0
		water_total_smp_reconstitution=0

		if item['type'] =="Shortage":

			procurement_of_month = 0
			try:
				diary=Diary.objects.get(name=item['diary'])
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)
				procurement_of_month = Awm_obj.targetProcurement
			except Exception as e:
				print "Exception handled wmBalancingReport in line 804"

			max_allowable_reconstitution = procurement_of_month * GeneralCalculation.objects.get(code=1).value / 100



			reconstitution_amount = 0



			if max_allowable_reconstitution < after_transfer_value:
				wm_purchase = after_transfer_value - max_allowable_reconstitution
				purchase_rate = GeneralCalculation.objects.get(code=8).value
				transaction_item={'transaction':"WM Purchased:" + str(wm_purchase) + ", Amount:" + str(
					wm_purchase * purchase_rate)}
				wm_after_stock_transfer.append(transaction_item)
				if current_diary == item['diary']:
					wm_purchase_union+=wm_purchase

				reconstitution_amount = max_allowable_reconstitution
			else:
				reconstitution_amount = max_allowable_reconstitution - after_transfer_value

			if reconstitution_amount != 0:

				reconstitution_from_smp = reconstitution_amount * GeneralCalculation.objects.get(code=2).value / 100
				try:

					quantity_of_water = 100 - qcReconstitutionValueSmp() - qsmpReconstitutionValueSmp()
					cream_ratio = qcReconstitutionValueSmp() / 100
					smp_ratio = qsmpReconstitutionValueSmp() / 100
					water_ratio = quantity_of_water / 100

					smp_total_smp_reconstitution = reconstitution_from_smp * smp_ratio
					cream_total_smp_reconstitution = reconstitution_from_smp * cream_ratio
					water_total_smp_reconstitution = reconstitution_from_smp * water_ratio

					transaction_item={'transaction':" WM Reconstituted From SMP:"+str(reconstitution_from_smp)}

					wm_after_stock_transfer.append(transaction_item)
				except Exception as e:
					print  "Exception Handled wmBalancingReport At 845 "

				reconstitution_from_wmp = reconstitution_amount * GeneralCalculation.objects.get(code=3).value / 100

				try:

					qw = GeneralCalculation.objects.get(code=18).value

					water_ratio_wmp=qw/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					wmp_ratio_wmp=qwmpReconstitutionValueWMP()/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())
					smp_ratio_wmp=(-1*qsmpReconstitutionValueWMP())/(qw+qwmpReconstitutionValueWMP()-qsmpReconstitutionValueWMP())

					water_total_wmp_reconstitution=reconstitution_from_wmp*water_ratio_wmp
					wmp_total_wmp_reconstitution=reconstitution_from_wmp*wmp_ratio_wmp
					smp_total_wmp_reconstitution=reconstitution_from_wmp*smp_ratio_wmp
				except Exception as e:
					print "Exception Handled wmBalancingReport At  861 "


				transaction_item={'transaction':" WM Reconstituted From WMP:" + str(
					reconstitution_from_wmp)}
				wm_after_stock_transfer.append(transaction_item)


		else:


			sale_percentage = GeneralCalculation.objects.get(code=4).value
			sale_rate = GeneralCalculation.objects.get(code=9).value

			wm_for_sale = after_transfer_value * sale_percentage / 100

			transaction_item={'transaction':" WM Sold:" + str(wm_for_sale) + ", Amount:" + str(
				wm_for_sale * sale_rate)}
			if current_diary == item['diary']:
				wm_sale_union+=wm_for_sale

			wm_after_stock_transfer.append(transaction_item)


			csm_convert_percentage = GeneralCalculation.objects.get(code=5).value
			wm_converted_to_csm = after_transfer_value * csm_convert_percentage / 100
			if item['diary']==current_diary:
				wm_converted_to_csm_union+=wm_converted_to_csm

			transaction_item={'transaction':" WM Converted to CSM:"+str(wm_converted_to_csm)}
			wm_after_stock_transfer.append(transaction_item)


			csm_wm_ratio = qwmValueCSM() / (qwmValueCSM() - qcValueCSM())
			csm_cream_ratio = -1 * (
			qcValueCSM() / (qwmValueCSM() - qcValueCSM()))

			csm_smp_conversion_percentage = GeneralCalculation.objects.get(code=7).value
			pcsm_for_conversion = wm_converted_to_csm / csm_wm_ratio

			wm_total_csm = wm_converted_to_csm
			if item['diary']==current_diary:
				wm_for_csm=+wm_total_csm
				cream_for_csm+=cream_total_csm


			cream_total_csm =  pcsm_for_conversion * csm_cream_ratio

			scsm = scsmCalculation()

			transaction_item={'transaction':" SNF Percentage of CSM:" + str(scsm)}

			wm_after_stock_transfer.append(transaction_item)

			csm_sale_percentage = GeneralCalculation.objects.get(code=6).value
			csm_sale_rate = GeneralCalculation.objects.get(code=10).value
			csm_sold = pcsm_for_conversion * csm_sale_percentage / 100
			csm_sold_amount = csm_sold * csm_sale_rate
			if current_diary == item['diary']:
				csm_sale_union+=csm_sold

			transaction_item={'transaction':" CSM Sold:" + str(csm_sold) + ", Amount:" + str(
				csm_sold_amount)}
			wm_after_stock_transfer.append(transaction_item)




			if item['diary']==current_diary:
				csm_for_conversion+=pcsm_for_conversion

			csm_converted_to_smp_display = pcsm_for_conversion * (csm_smp_conversion_percentage / 100)
			csm_converted_to_smp =psmpCalculation(csm_converted_to_smp_display)

			if item['diary']==current_diary:
				smp_from_conversion += csm_converted_to_smp



			transaction_item={'transaction':" CSM Converted to SMP:" + str(csm_converted_to_smp_display)}
			wm_after_stock_transfer.append(transaction_item)

		if current_diary==item['diary']:
			wm_reconstitution_union+=reconstitution_amount
			cream_reconstitution_union+=cream_total_smp_reconstitution
			smp_rc_smp_union +=smp_total_smp_reconstitution
			smp_rc_wmp_union+=smp_total_wmp_reconstitution
			water_rc_smp_union+=water_total_smp_reconstitution
			water_rc_wmp_union+=water_total_wmp_reconstitution
			wmp_rc_wmp_union+=wmp_total_wmp_reconstitution





		resultitem={'diary':item['diary'],'after_transfer':str(item['type'])+" : "+str(item['value']),'transactions':wm_after_stock_transfer,'wmp_used':wmp_total_wmp_reconstitution
			,'smp_used_smp':smp_total_smp_reconstitution,'smp_used_wmp':smp_total_wmp_reconstitution,'converted_smp':csm_converted_to_smp,'cream_used_csm':cream_total_csm
					,'cream_used_smp':cream_total_smp_reconstitution,'wm_used_csm':wm_total_csm,'water_used_wmp':water_total_wmp_reconstitution
					,'water_used_smp':water_total_smp_reconstitution}
		wm_balanced_diarylist.append(resultitem)




	return wm_balanced_diarylist,wm_reconstitution_union,wm_purchase_union,wm_sale_union,csm_sale_union,smp_from_conversion,cream_reconstitution_union,smp_from_conversion,wm_for_csm,smp_rc_smp_union,smp_rc_wmp_union,water_rc_smp_union,water_rc_wmp_union,wmp_rc_wmp_union,cream_for_csm,wm_converted_to_csm_union,csm_for_conversion



def interCreamTransfer(shortage_list,surplus_list,diaryList):
	resultitem = []



	inter_stock_transfer_list=InterStockCreamTransferOrder.objects.all()

	# print str(shortage_list)
	# print str(surplus_list)


	for item in inter_stock_transfer_list:
		from_diary= str(item.from_diary.name)
		to_diary=str(item.to_diary.name)

		if from_diary in surplus_list.keys() and to_diary in shortage_list.keys():
			if surplus_list[from_diary]> shortage_list[to_diary]:
				difference=surplus_list[from_diary]-shortage_list[to_diary]

				result = {"fromdiary":from_diary,"todiary":to_diary,"value":shortage_list[to_diary]}
				surplus_list[from_diary] = difference
				del shortage_list[to_diary]
				# print str(surplus_list)
				# print str(shortage_list)
			else:



				difference=shortage_list[to_diary]-surplus_list[from_diary]


				result = {"fromdiary": from_diary, "todiary": to_diary, "value": surplus_list[from_diary]}
				shortage_list[to_diary] = difference

				del surplus_list[from_diary]


			resultitem.append(result)






	# print "surplus"
	# print surplus_list
	# print "shortage"
	# print shortage_list

	diary_after_stock_transfer=[]
	if bool(surplus_list):

		for item,value in surplus_list.items():
			result={'diary':item,'value':value,'type':"Surplus"}
			diary_after_stock_transfer.append(result)



	if bool(shortage_list):
		for item, value in shortage_list.items():
			result = {'diary': item, 'value': value,'type':"Shortage"}
			diary_after_stock_transfer.append(result)







	stock_transfer=[]
	for diary in diaryList:




		for item in resultitem:
			if diary.name==item['fromdiary'] or diary.name==item['todiary']:
				if item['fromdiary']==diary.name:
					transfer_type="to"
					to_or_from_diary=item['todiary']

				elif item['todiary']==diary.name:
					transfer_type="from"
					to_or_from_diary=item['fromdiary']

				result={"diary":diary.name,"type":transfer_type,"to_or_from_diary":to_or_from_diary,"value":item['value']}
				stock_transfer.append((result))




	# print stock_transfer

	return diary_after_stock_transfer,stock_transfer


def creamBalancing(after_transfer_diary_list):
	cream_balanced_diarylist = []
	for item in after_transfer_diary_list:
		after_transfer_value = item['value']

		cream_after_stock_transfer=""
		if item['type'] == "Shortage":
			try:
				cream_after_stock_transfer=" Cream Purchased:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=15).value)
			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""
		else:
			try:
				cream_after_stock_transfer=" Cream sold:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=16).value)
			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""



		resultitem = {'diary': item['diary'],
					  'after_transfer': str(item['type']) + " : " + str(after_transfer_value),
					  'transactions': cream_after_stock_transfer}
		cream_balanced_diarylist.append(resultitem)
	return cream_balanced_diarylist

def creamBalancingReport(after_transfer_diary_list):
	cream_balanced_diarylist = []

	cream_purchased=0
	cream_sold=0

	for item in after_transfer_diary_list:
		after_transfer_value = item['value']

		cream_after_stock_transfer=""
		if item['type'] == "Shortage":
			try:
				cream_after_stock_transfer=" Cream Purchased:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=15).value)
				cream_purchased+=after_transfer_value

			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""
		else:
			try:
				cream_after_stock_transfer=" Cream sold:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=16).value)
				cream_sold+=after_transfer_value
			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""



		resultitem = {'diary': item['diary'],
					  'after_transfer': str(item['type']) + " : " + str(after_transfer_value),
					  'transactions': cream_after_stock_transfer}
		cream_balanced_diarylist.append(resultitem)
	return cream_balanced_diarylist,cream_purchased,cream_sold

def creamBalancingReportFinance(after_transfer_diary_list):
	cream_balanced_diarylist = []

	cream_purchased=0
	cream_sold=0

	cream_purchase_list=[]

	for item in after_transfer_diary_list:
		cream_Amount=0
		after_transfer_value = item['value']

		cream_after_stock_transfer=""

		if item['type'] == "Shortage":
			try:
				cream_Amount=after_transfer_value*GeneralCalculation.objects.get(code=15).value
				cream_after_stock_transfer=" Cream Purchased:"+str(after_transfer_value)+" ,Amount:"+str(cream_Amount)
				cream_purchased+=after_transfer_value

			except Exception as e:
				print "Exception Handled At 1492"
			cream_after_stock_transfer+=""
		else:
			try:
				cream_after_stock_transfer=" Cream sold:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=16).value)
				cream_sold+=after_transfer_value
			except Exception as e:
				print "Exception Handled At 1499"
			cream_after_stock_transfer+=""



		resultitem = {'diary': item['diary'],
					  'after_transfer': str(item['type']) + " : " + str(after_transfer_value),
					  'transactions': cream_after_stock_transfer}
		cream_balanced_diarylist.append(resultitem)

		cream_purchase_item={'diary': item['diary'],'Amount':cream_Amount}
		cream_purchase_list.append(cream_purchase_item)
	return cream_balanced_diarylist,cream_purchase_list

def creamBalancingReportDiaryWise(after_transfer_diary_list,current_diary):
	cream_balanced_diarylist = []

	cream_purchased=0
	cream_sold=0

	for item in after_transfer_diary_list:
		after_transfer_value = item['value']

		cream_after_stock_transfer=""
		if item['type'] == "Shortage":
			try:
				cream_after_stock_transfer=" Cream Purchased:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=15).value)
				if item['diary'].name==current_diary:
					cream_purchased+=after_transfer_value

			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""
		else:

			try:
				cream_after_stock_transfer=" Cream sold:"+str(after_transfer_value)+" ,Amount:"+str(after_transfer_value*GeneralCalculation.objects.get(code=16).value)
				if item['diary'].name == current_diary:
					cream_sold+=after_transfer_value
			except Exception as e:
				print "Exception Handled At 848"
			cream_after_stock_transfer+=""



		resultitem = {'diary': item['diary'],
					  'after_transfer': str(item['type']) + " : " + str(after_transfer_value),
					  'transactions': cream_after_stock_transfer}
		cream_balanced_diarylist.append(resultitem)
	return cream_balanced_diarylist,cream_purchased,cream_sold


