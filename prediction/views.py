# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .forms import *
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
#from .models import Variant,Product,ProductCategoryGrowthFactor,Composition,Issue,ActualStockin,ActualSale,Diary,Category,MethodPercentage,IssueAsCategory,UserDiaryLink
from .models import *
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.utils.dates import MONTHS
from .functions import *
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.template import RequestContext
from collections import OrderedDict

from threading import Thread
import timeit
import time






# Create your views here.


def diary_of_user(user):
	try:
		user_diary_link_obj=UserDiaryLink.objects.get(user=user)
	except UserDiaryLink.DoesNotExist:
		user_diary_link_obj=None
		print "Exception handled:User not linked with any diary"

	return user_diary_link_obj.diary
def getMethodPercentage(category,method):
	method_list=category.distinctMethodList
	method_percentage_list=MethodPercentage.objects.filter(category=category,method=method)

	#Method Percentage Validation
	print "Method Count from Composition:"+str(method_list.count())
	print "Method Count from MethodPercentage:",MethodPercentage.objects.filter(category=category).count()
	if (MethodPercentage.objects.filter(category=category).count()!=method_list.count()) and method_list.count()!=1:

		return 0

	if len(method_percentage_list) ==0:
		return 100
	else:
		return method_percentage_list[0].percentage
def group_check_diary(user):
	return user.groups.filter(name='Diary')
def group_check_union(user):
	return user.groups.filter(name='Union')
def user_diary_link_check(user):
	return UserDiaryLink.objects.filter(user=user)

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



@login_required
@user_passes_test(group_check_diary)
def issuerequirement(request):
	if request.method == "POST":
		form = IssueRequirementForm(request.POST)
		if form.is_valid():
			#diary = form.save(commit=False)
			#diary.save()

			issue=form.cleaned_data["issue"]
			#month=form.cleaned_data["month"]

			diary=diary_of_user(request.user)
			#CategoryList=Category.objects.all()
			issue_requirement=0


			# issue_monthwise={}
			issue_monthwise = OrderedDict()

			# issue_as_product={}
			issue_as_product =OrderedDict()


			# issue_as_issue={}
			issue_as_issue =OrderedDict()


			#global requested_issue
			for month in MONTHS.items():

				print month[1]
				ret_month,month_issue_requirement=totalIssueRequirement(month[0],diary,issue)
				# messages.info(request,str(month[1])+"---"+str(month_issue_requirement))
				issue_monthwise[ret_month]=month_issue_requirement

				ret_issueasproduct_month,issue_as_product_requirement=IssueasProduct(month[0],diary,issue)
				issue_as_product[ret_issueasproduct_month]=issue_as_product_requirement

				issue_as_issue[month[1]]=month_issue_requirement-issue_as_product_requirement

				# messages.info(request, month[1]+"value:"+str(issue_as_product_requirement))
				#issue_requirement=totalIssueRequirement(month[0],diary,issue)

				#issue_monthwise.append({month[1]:issue_requirement})



			# print issue_monthwise
			return render(request, "prediction/IssueWise.html",{"issue_monthwise":issue_monthwise,'form':form,'issue_as_product':issue_as_product,'issue_as_issue':issue_as_issue})

	else:
		form = IssueRequirementForm()
	#return render(request, 'prediction/issue_requirement.html', {'form': form})
	return render(request, 'prediction/IssueWise.html', {'form': form})


@login_required
@user_passes_test(group_check_diary)
def basicRequirement(request):
	if request.method == "POST":
		form = IssueRequirementFormBasic(request.POST)
		if form.is_valid():
			issue_id=form.cleaned_data["issue"]


			issue=Issue.objects.get(id=issue_id)

			diary=diary_of_user(request.user)

			# total_requirement={}
			total_requirement = OrderedDict()

			fwm = Issue.objects.get(name='WM').fat


			for month in MONTHS.items():

				# print month[1]
				# messages.info(request,"issue"+str(issue)+"diary"+str(diary)+"month"+str(month[0]))
				# start = timeit.default_timer()

				ret_month,month_issue_requirement_plus_sales=totalIssueRequirement(month[0],diary,issue)
				# stop = timeit.default_timer()

				# print str(diary.name) + "---" + str(month[1]) + "  " + str(stop - start)


				month_requirement_for_milk_issue_production=0
				type2_issue_list=Issue.objects.filter(type='2')


				for issue_item in type2_issue_list:



					issue_ret_month,month_issue_requirement=totalIssueRequirement(month[0],diary,issue_item)

					composition_ratio_derived=0
					if issue.name=="CREAM":
						try:

							if issue_item.fat>fwm:
								composition_ratio_derived=qcValue(issue_item)/(qcValue(issue_item)+qwmValue(issue_item)+qsmpValue(issue_item))
							else:
								composition_ratio_derived =-1*( qcValue(issue_item) / (
									(qwmValue(issue_item)-qcValue(issue_item))   + qsmpValue(issue_item)))

						except Exception as e:
							print "Exception handled in line no 142"

					elif issue.name=="WM":
						try:
							if issue_item.fat > fwm:
								composition_ratio_derived=qwmValue(issue_item)/(qcValue(issue_item)+qwmValue(issue_item)+qsmpValue(issue_item))
							else:
								composition_ratio_derived = qwmValue(issue_item) / (
									(qwmValue(issue_item)-qcValue(issue_item) )  + qsmpValue(issue_item))
							# messages.info(request, "Month-" + str(month[1]) + " Issue-" + str(issue_item) + " Qsmp:" + str(
							# 	qsmpValue(issue_item)) + " Qc:" + str(qcValue(issue_item)) + " Qwm:" + str(
							# 	qwmValue(issue_item)))
						except Exception as e:
							print "Exception handled in line no 152"


					elif issue.name=="SMP":
						try:
							# messages.info(request, "Month" + str(month[1]) + " Issue" + str(issue_item) + " Qsmp:" + str(
							# 	qsmpValue(issue_item)) + " Qc:" + str(qcValue(issue_item)) + " Qwm:" + str(
							# 	qwmValue(issue_item)))
							if issue_item.fat > fwm:
								composition_ratio_derived=qsmpValue(issue_item)/(qcValue(issue_item)+qwmValue(issue_item)+qsmpValue(issue_item))
							else:
								composition_ratio_derived = qsmpValue(issue_item) / (
									(qwmValue(issue_item)-qcValue(issue_item)) + qsmpValue(issue_item))
						except Exception as e:
							 print "Exception handled in line no 163"


					requirement_to_produce_milk_issue=month_issue_requirement*composition_ratio_derived
					# messages.info(request,
					# 			  "Month" + str(month[1]) + "  Milk requirement  " + str(requirement_to_produce_milk_issue) + str(issue_item)+"  compo:"+str(composition_ratio_derived))

					month_requirement_for_milk_issue_production+=requirement_to_produce_milk_issue


					# messages.info(request,"Month"+str(month[1])+"   "+str(month_issue_requirement)+"Issue"+str(issue_item))


				# messages.info(request,"Month"+str(month[1])+"-Milk-"+str(month_requirement_for_milk_issue_production)+"-Issue-"+str(month_issue_requirement_plus_sales))
				total_month_requirement=month_requirement_for_milk_issue_production + month_issue_requirement_plus_sales
				# stop = timeit.default_timer()

				# print "Time-------------------" + str(stop - start)
				# total_month_requirement = month_requirement_for_milk_issue_production



				total_requirement[month[1]]=total_month_requirement
			# stop = timeit.default_timer()
            #
			# print str(diary.name) + "---" + str(issue.name) + "  " + str(stop - start)

			return render(request, "prediction/IssueWiseBasic.html",{"issue_monthwise":total_requirement,'form':form})

	else:
		form = IssueRequirementFormBasic()
	#return render(request, 'prediction/issue_requirement.html', {'form': form})
	return render(request, 'prediction/IssueWiseBasic.html', {'form': form})

@login_required
@user_passes_test(group_check_union)
def basicRequirementUnion(request):
	if request.method == "POST":
		form = IssueRequirementFormBasic(request.POST)

		if form.is_valid():
			issue_id=form.cleaned_data["issue"]

			issue=Issue.objects.get(id=issue_id)

			total_requirement_union =OrderedDict()
			# total_requirement_union={}

			fwm = Issue.objects.get(name='WM').fat



			# try:
			# 	Config_Attribute_obj=ConfigurationAttribute.objects.first()
			# 	issue_requirement_change_status=Config_Attribute_obj.issue_requirement_change_status
			# except Exception as e:
			# 	print "Exception Due to Configuration Attribute Not Entered-269"
			# 	issue_requirement_change_status=False


			for month in MONTHS.items():
				print month[1]
				diary_list=Diary.objects.all()
				total_requirement_diary = 0
				for diary in diary_list:

					ret_month,month_issue_requirement_plus_sales=totalIssueRequirement(month[0],diary,issue)



					# if issue_requirement_change_status:
					# 	issueRequirementDB(diary,month[0],issue)
					# 	Issue_list = Issue.objects.filter(type='2')
                    #
					# 	for issue_item in Issue_list:
					# 		issueRequirementDB(diary, month[0], issue_item)
					# 	Config_Attribute_obj.issue_requirement_change_status=False
					# 	Config_Attribute_obj.save()
                    #
                    #
                    #
                    #
					# try:
                    #
					# 	month_issue_requirement_plus_sales = IssueRequirement.objects.get(month=month[0], diary=diary,
					# 														   issue=issue).requirement
					# except Exception as e:
					# 	month_issue_requirement_plus_sales = 0



					month_requirement_for_milk_issue_production=0
					type2_issue_list=Issue.objects.filter(type='2')
					# start = timeit.default_timer()
					for issue_item in type2_issue_list:

						issue_ret_month,month_issue_requirement=totalIssueRequirement(month[0],diary,issue_item)

						# try:
                        #
						# 	month_issue_requirement=IssueRequirement.objects.get(month=month[0],diary=diary,issue=issue_item).requirement
						# except Exception as e:
						# 	month_issue_requirement=0

						composition_ratio_derived=0
						if issue.name == "CREAM":
							try:

								if issue_item.fat > fwm:
									composition_ratio_derived = qcValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
								else:
									composition_ratio_derived = -1 * (qcValue(issue_item) / (
										(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item)))

							except Exception as e:
								print "Exception handled in line no 142"

						elif issue.name == "WM":
							try:
								if issue_item.fat > fwm:
									composition_ratio_derived = qwmValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
								else:
									composition_ratio_derived = qwmValue(issue_item) / (
										(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))
							except Exception as e:
								print "Exception handled in line no 152"


						elif issue.name == "SMP":
							try:

								if issue_item.fat > fwm:
									composition_ratio_derived = qsmpValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
								else:
									composition_ratio_derived = qsmpValue(issue_item) / (
										(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))
							except Exception as e:
								print "Exception handled in line no 163"


						requirement_to_produce_milk_issue=month_issue_requirement*composition_ratio_derived
						month_requirement_for_milk_issue_production+=requirement_to_produce_milk_issue
					# stop = timeit.default_timer()

					# print str(month[1]) + "   Time of"+ str(diary.name) + " "+ str(stop - start)
					total_month_requirement=month_requirement_for_milk_issue_production + month_issue_requirement_plus_sales
					# total_month_requirement = month_requirement_for_milk_issue_production

					# total_requirement_union[month[1]]=total_month_requirement
					total_requirement_diary+=total_month_requirement
				total_requirement_union[month[1]] = total_requirement_diary
				# messages.info(request,"Requirement:"+str(total_requirement_diary)+"Month:"+str(month[1]))





			return render(request, "prediction/IssueWiseBasicUnion.html",{"total_requirement_union":total_requirement_union,'form':form})


	else:
		form = IssueRequirementFormBasic()


	#return render(request, 'prediction/issue_requirement.html', {'form': form})
	return render(request, 'prediction/IssueWiseBasicUnion.html', {'form': form})



@login_required
@user_passes_test(group_check_union)
def basicRequirementUnionDiaryWise(request):
	if request.method == "POST":

		form_union = IssueRequirementFormBasicUnion(request.POST)
		if form_union.is_valid():
			issue_id=form_union.cleaned_data["issue"]

			issue=Issue.objects.get(id=issue_id)

			diary=form_union.cleaned_data["diary"]


			# total_requirement={}
			total_requirement =OrderedDict()


			fwm = Issue.objects.get(name='WM').fat

			for month in MONTHS.items():

				# print month[1]
				ret_month,month_issue_requirement_plus_sales=totalIssueRequirement(month[0],diary,issue)



				month_requirement_for_milk_issue_production=0
				type2_issue_list=Issue.objects.filter(type='2')
				for issue_item in type2_issue_list:

					# try:
                    #
					# 	month_issue_requirement = IssueRequirement.objects.get(month=month[0], diary=diary,
					# 														   issue=issue_item).requirement
					# except Exception as e:
					# 	month_issue_requirement = 0
					issue_ret_month,month_issue_requirement=totalIssueRequirement(month[0],diary,issue_item)

					composition_ratio_derived=0
					if issue.name == "CREAM":
						try:

							if issue_item.fat > fwm:
								composition_ratio_derived = qcValue(issue_item) / (
								qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
							else:
								composition_ratio_derived = -1 * (qcValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item)))

						except Exception as e:
							print "Exception handled in line no 142"

					elif issue.name == "WM":
						try:
							if issue_item.fat > fwm:
								composition_ratio_derived = qwmValue(issue_item) / (
								qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
							else:
								composition_ratio_derived = qwmValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))
						except Exception as e:
							print "Exception handled in line no 152"


					elif issue.name == "SMP":
						try:
							if issue_item.fat > fwm:
								composition_ratio_derived = qsmpValue(issue_item) / (
								qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
							else:
								composition_ratio_derived = qsmpValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))
						except Exception as e:
							print "Exception handled in line no 163"


					requirement_to_produce_milk_issue=month_issue_requirement*composition_ratio_derived
					month_requirement_for_milk_issue_production+=requirement_to_produce_milk_issue
				total_month_requirement=month_requirement_for_milk_issue_production + month_issue_requirement_plus_sales

				# total_month_requirement = month_requirement_for_milk_issue_production
				total_requirement[month[1]]=total_month_requirement

			return render(request, "prediction/IssueWiseBasicUnionDiaryWise.html",{"issue_monthwise":total_requirement,'form_union':form_union})


	else:

		form_union = IssueRequirementFormBasicUnion()

	#return render(request, 'prediction/issue_requirement.html', {'form': form})
	return render(request, 'prediction/IssueWiseBasicUnionDiaryWise.html', {'form_union':form_union})



@login_required
@user_passes_test(group_check_union)
def variantNew(request):
	variantList=Variant.objects.all().order_by('name')
	if request.method == "POST":
		form = VariantForm(request.POST)
		if request.POST.get('delete',False):

			if form.is_valid():

				try:
					Variant.objects.get(name=str(form.cleaned_data["first_name"])+str(form.cleaned_data["unit_name"]),unit=form.cleaned_data["unit"]).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(variantNew)
		if form.is_valid():
			#variant = form.save(commit=False)

			data = form.cleaned_data

			"""obj, created = Variant.objects.update_or_create(
					name=data['name'],
					defaults={'unit':data['unit']},

				)"""
			try:
				variant=Variant(name=str(data['first_name'])+str(data['unit_name']),unit=data['unit'])
				variant.save()
			except Exception as e:
				messages.info(request, "Already Exist")
			return redirect(variantNew)
	else:
		form = VariantForm()
	return render(request, 'prediction/Variant.html', {'form': form,'variantList':variantList})

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


@login_required
@user_passes_test(group_check_union)
def productNew(request):
	productList=Product.objects.all().order_by('code')
	if request.method == "POST":
		form = ProductForm(request.POST)
		if request.POST.get('delete',False):
			if form.is_valid():

				try:
					Product.objects.get(code=form.cleaned_data["code"],category=form.cleaned_data["category"],variant=form.cleaned_data["variant"]).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(productNew)

		"""if form.is_valid():
			product=form.save(commit=False)
			product.save()"""
		if form.is_valid():

			data = form.cleaned_data




			if data['category'].specific_gravity==1:
				obj, created = Product.objects.update_or_create(code=data['code'],
																defaults={'category':data['category'],'variant': data['variant'],'rate':data['rate']},
				)
			else:
				if ("l" in str(data['variant'].name)) or ("L" in str(data['variant'].name)):
					obj, created = Product.objects.update_or_create(
						code=data['code'],
						defaults={'category':data['category'],'variant': data["variant"],'rate': data['rate']},

					)
				else:
					messages.info(request,"Please Check The Selected Variant")






				return redirect(productNew)
	else:
		form=ProductForm()
	return render(request,'prediction/Product.html',{'form':form,'productList':productList})



@login_required
@user_passes_test(group_check_union)
def issueNew(request):
	issueList=Issue.objects.all().order_by('id')
	if request.method == "POST":
		form = IssueForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			issue_obj=Issue.objects.get(id=data['issue'].id)
			issue_obj.fat=data['fat']
			issue_obj.snf=data['snf']
			issue_obj.save()
			# obj= issue_obj.update(
			#         fat=data['fat'],snf=data['snf'],
			#
			#     )

			return redirect(issueNew)
	else:
		form=IssueForm()
	return render(request,'prediction/Issue.html',{'form':form,'issueList':issueList})

@login_required
@user_passes_test(group_check_union)
def compositionNew(request):
	compositionList=Composition.objects.all().order_by('category')
	if request.method == "POST":
		form = CompositionForm(request.POST)
		if request.POST.get('delete',False):

			if form.is_valid():

				try:


					Composition.objects.get(category=form.cleaned_data["category"],method=form.cleaned_data["method"],issue=form.cleaned_data["issue"]).delete()
					messages.info(request, "Successfully Deleted")
					# try:
					# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
					# 	Config_Attribute_obj.issue_requirement_change_status = True
					# 	Config_Attribute_obj.save()
					# except Exception as e:
					# 	print "Exception Handled At 614"
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(compositionNew)

		"""if form.is_valid():
			composition=form.save(commit=False)
			composition.save()"""
		if form.is_valid():

			data = form.cleaned_data
			if data['category'].name == "GHEE" or data['category'].name=="BUTTER":
				messages.info(request,"Ratio Is Auto Generated")

			obj, created = Composition.objects.update_or_create(
					method=data['method'],category=data['category'],issue=data["issue"],
					defaults={'ratio':data['ratio']},

				)
			# try:
			# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
			# 	Config_Attribute_obj.issue_requirement_change_status = True
			# 	Config_Attribute_obj.save()
			# except Exception as e:
			# 	print "Exception Handled At 634"


			return redirect(compositionNew)
	else:
		form=CompositionForm()
	return render(request,'prediction/Composition.html',{'form':form,'compositionList':compositionList})


@login_required
@user_passes_test(group_check_union)
def methodpercentageNew(request):
	method_percentage_List=MethodPercentage.objects.all().order_by('category')
	if request.method == "POST":
		form = MethodPercentageForm(request.POST)

		if request.POST.get('delete',False):

			if form.is_valid():
				try:

					MethodPercentage.objects.get(category=form.cleaned_data["category"],method=form.cleaned_data["method"]).delete()
					messages.info(request, "Successfully Deleted")
					# try:
					# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
					# 	Config_Attribute_obj.issue_requirement_change_status = True
					# 	Config_Attribute_obj.save()
					# except Exception as e:
					# 	print "Exception Handled At 662"
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(methodpercentageNew)

		"""if form.is_valid():
			method_percentage=form.save(commit=False)
			method_percentage.save()
			return redirect(methodpercentageNew)"""
		if form.is_valid():
			data = form.cleaned_data
			obj, created = MethodPercentage.objects.update_or_create(
					method=data['method'],category=data['category'],
					defaults={'percentage':data['percentage']},

				)
			# try:
			# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
			# 	Config_Attribute_obj.issue_requirement_change_status = True
			# 	Config_Attribute_obj.save()
			# except Exception as e:
			# 	print "Exception Handled At 677"
			return redirect("methodpercentageNew")
	else:
		form=MethodPercentageForm()
	return render(request,'prediction/MethodPercentage.html',{'form':form,'method_percentage_List':method_percentage_List})

@login_required
@user_passes_test(group_check_union)
def fatPercentageYield(request):
	fat_percentage_yield_List=FatPercentageYield.objects.all().order_by('category')
	if request.method == "POST":
		form = FatPercentageYieldForm(request.POST)

		if request.POST.get('delete',False):

			if form.is_valid():
				try:

					FatPercentageYield.objects.get(category=form.cleaned_data["category"],issue=form.cleaned_data["issue"],method=form.cleaned_data["method"]).delete()
					messages.info(request, "Successfully Deleted")
					# try:
					# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
					# 	Config_Attribute_obj.issue_requirement_change_status = True
					# 	Config_Attribute_obj.save()
					# except Exception as e:
					# 	print "Exception Handled At 703"
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(fatPercentageYield)


		#  if form.is_valid():
		#      method_percentage=form.save(commit=False)
		#      method_percentage.save()
		#      return redirect(fatPercentageYield)
		if form.is_valid():


			data = form.cleaned_data
			obj, created = FatPercentageYield.objects.update_or_create(
					 method=data['method'],category=data['category'],issue=data['issue'],
					 defaults={'percentage':data['percentage']},

			)
			# try:
			# 	Config_Attribute_obj = ConfigurationAttribute.objects.first()
			# 	Config_Attribute_obj.issue_requirement_change_status = True
			# 	Config_Attribute_obj.save()
			# except Exception as e:
			# 	print "Exception Handled At 722"
		return redirect(fatPercentageYield)
	else:
		form=FatPercentageYieldForm()
	return render(request,'prediction/FatPercentageYield.html',{'form':form,'fat_percentage_yield_List':fat_percentage_yield_List})

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

@login_required
@user_passes_test(group_check_diary)
# @user_passes_test(user_diary_link_check)
def targetYear(request):
	diary=diary_of_user(request.user)

	actualProductSales=ActualSale.objects.filter(diary=diary).order_by('month')
	actualProductStockIn=ActualStockin.objects.filter(diary=diary).order_by('month')
	actualProductStockOut=ActualStockin.objects.filter(from_diary=diary).order_by('month')
	targetWMProcurement=ActualWMProcurement.objects.filter(diary=diary).order_by('month')
	return render(request,'prediction/Targetyear.html',{'actualProductSales':actualProductSales,'actualProductStockIn':actualProductStockIn,'actualProductStockOut':actualProductStockOut,'targetWMProcurement':targetWMProcurement})

@login_required
@user_passes_test(group_check_union)
def targetYearUnion(request):

	actualProductSales=ActualSale.objects.all().order_by('month')
	actualProductStockIn=ActualStockin.objects.all().order_by('month')
	actualProductStockOut=ActualStockin.objects.all().order_by('month')
	targetWMProcurement=ActualWMProcurement.objects.all().order_by('month')
	return render(request,'prediction/TargetyearUnion.html',{'actualProductSales':actualProductSales,'actualProductStockIn':actualProductStockIn,'actualProductStockOut':actualProductStockOut,'targetWMProcurement':targetWMProcurement})


@login_required
@user_passes_test(group_check_diary)
def growthFactorEntry(request):
	diary=diary_of_user(request.user)
	productGrowthFactor=ProductCategoryGrowthFactor.objects.filter(diary=diary).order_by('month','category')
	procurementGrowthFactor=ProcurementGrowthFactor.objects.filter(diary=diary).order_by('month','diary')

		#return HttpResponse('delete')
		#print "hello"

	if request.method == "POST":
		form = ProductCategoryGrowthFactorForm(request.POST)
		form_procurement=ProcurementGrowthFactorForm(request.POST)
		if request.POST.get('delete',False):

			if form_procurement.is_valid():
				try:
					ProcurementGrowthFactor.objects.get(month=form_procurement.cleaned_data["month"],diary=diary).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")
			return redirect("/growthfactorentry/#procurement")


		if request.POST.get('delete_product_growth_factor',False):

			if form.is_valid():
				try:
					ProductCategoryGrowthFactor.objects.get(month=form.cleaned_data["month"],diary=diary,category=form.cleaned_data["category"]).delete()
					messages.info(request, "Successfully Deleted")
					# t = Thread(target=totalIssueRequirementDB, args=(diary, form.cleaned_data['month'], form.cleaned_data['category']))
					# t.start()
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/growthfactorentry/#product")


		if form.is_valid():
			data = form.cleaned_data
			obj, created = ProductCategoryGrowthFactor.objects.update_or_create(
					diary=diary,month=data['month'],category=data['category'],
					defaults={'growth_factor':data['growth_factor']},

				)
			# t = Thread(target=totalIssueRequirementDB, args=(diary, data['month'],data['category'] ))
			# t.start()
			return redirect("/growthfactorentry/#product")
		if form_procurement.is_valid():
			data = form_procurement.cleaned_data
			obj, created = ProcurementGrowthFactor.objects.update_or_create(
					diary=diary,month=data['month'],
					defaults={'growth_factor':data['growth_factor']},

				)
			return redirect("/growthfactorentry/#procurement")
		"""if form.is_valid():

			try:
				product_category_growth_factor=form.save(commit=False)
				product_category_growth_factor.diary=diary
				product_category_growth_factor.save()
				#return HttpResponseRedirect(request,'prediction/GrowthFactorEntry.html',{'form':form,'productGrowthFactor':productGrowthFactor})

			except Exception as e:
				print "Product growth factor with this Month and Diary already exists."


		if form_procurement.is_valid():

			try:
				procurement_growth_factor=form_procurement.save(commit=False)
				procurement_growth_factor.diary=diary
				procurement_growth_factor.save()

			except Exception as e:
				print "Procurement growth factor with this Month and Diary already exists."
				"""
		#return redirect(growthFactorEntry)


			#return HttpResponseRedirect(request,'prediction/GrowthFactorEntry.html',{'form_procurement':form_procurement,'procurementGrowthFactor':procurementGrowthFactor})
	else:
		form=ProductCategoryGrowthFactorForm()
		form_procurement=ProcurementGrowthFactorForm()
	#return render(request,'prediction/all_new.html',{'form':form,'name':"Product Category Growth Factor"})
	return render(request,'prediction/GrowthFactorEntry.html',{'form_procurement':form_procurement,'form':form,'productGrowthFactor':productGrowthFactor,'procurementGrowthFactor':procurementGrowthFactor})
	#return render(request,'prediction/GrowthFactorEntry.html',{'form_procurement':form_procurement,'procurementGrowthFactor':procurementGrowthFactor})

@login_required
@user_passes_test(group_check_union)
def growthFactorEntryUnion(request):

	productGrowthFactor=ProductCategoryGrowthFactor.objects.all().order_by('month','category')
	procurementGrowthFactor=ProcurementGrowthFactor.objects.all().order_by('month','diary')
	if request.method == "POST":
		form = ProductCategoryGrowthFactorFormUnion(request.POST)
		form_procurement=ProcurementGrowthFactorFormUnion(request.POST)
		if request.POST.get('delete',False):

			if form_procurement.is_valid():
				try:
					ProcurementGrowthFactor.objects.get(month=form_procurement.cleaned_data["month"],diary=form_procurement.cleaned_data["diary"]).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")
			return redirect("/growthfactorentryUnion/#procurement")


		if request.POST.get('delete_product_growth_factor',False):

			if form.is_valid():
				try:
					ProductCategoryGrowthFactor.objects.get(month=form.cleaned_data["month"],diary=form.cleaned_data["diary"],category=form.cleaned_data["category"]).delete()
					messages.info(request, "Successfully Deleted")
					# t = Thread(target=totalIssueRequirementDB, args=(form.cleaned_data['diary'], form.cleaned_data['month'], form.cleaned_data['category']))
					# t.start()
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/growthfactorentryUnion/#product")


		if form.is_valid():
			data = form.cleaned_data
			obj, created = ProductCategoryGrowthFactor.objects.update_or_create(
					diary=data['diary'],month=data['month'],category=data['category'],
					defaults={'growth_factor':data['growth_factor']},

				)
			# t = Thread(target=totalIssueRequirementDB, args=(data['diary'], data['month'],data['category'] ))
			# t.start()

			return redirect("/growthfactorentryUnion/#product")
		if form_procurement.is_valid():
			data = form_procurement.cleaned_data

			obj, created = ProcurementGrowthFactor.objects.update_or_create(
					diary=data['diary'],month=data['month'],
					defaults={'growth_factor':data['growth_factor']},

				)
			return redirect("/growthfactorentryUnion/#procurement")
			"""
			try:
				#product_category_growth_factor=form.save(commit=False)

				product_category_growth_factor_obj= ProductCategoryGrowthFactor.objects.get(diary=data['diary'],month=data['month'],category=data['category'])
				#print product_category_growth_factor_obj
				product_category_growth_factor_obj.growth_factor=data['growth_factor']
				product_category_growth_factor_obj.save()
				#return HttpResponseRedirect(request,'prediction/GrowthFactorEntry.html',{'form':form,'productGrowthFactor':productGrowthFactor})
				print 'updated'
			except Exception as e:
				product_category_growth_factor_obj= ProductCategoryGrowthFactor(diary=data['diary'],month=data['month'],category=data['category'],growth_factor=data['growth_factor'])
				product_category_growth_factor_obj.save()
				print "created"
				#print " 490 Product growth factor with this Month and Diary already exists.",e
			"""


			"""try:
				procurement_growth_factor=form_procurement.save(commit=False)
				procurement_growth_factor.save()

			except Exception as e:
				print "499 Procurement growth factor with this Month and Diary already exists."
				"""

		#return redirect(growthFactorEntryUnion)

			#return HttpResponseRedirect(request,'prediction/GrowthFactorEntry.html',{'form_procurement':form_procurement,'procurementGrowthFactor':procurementGrowthFactor})
	else:
		form=ProductCategoryGrowthFactorFormUnion()
		form_procurement=ProcurementGrowthFactorFormUnion()
	#return render(request,'prediction/all_new.html',{'form':form,'name':"Product Category Growth Factor"})
	return render(request,'prediction/GrowthFactorEntryUnion.html',{'form_procurement':form_procurement,'form':form,'productGrowthFactor':productGrowthFactor,'procurementGrowthFactor':procurementGrowthFactor})
	#return render(request,'prediction/GrowthFactorEntry.html',{'form_procurement':form_procurement,'procurementGrowthFactor':procurementGrowthFactor})


@login_required
@user_passes_test(group_check_union)
def productConfiguration(request):
	productConfigurationList=ProductConfiguration.objects.all().order_by('diary')
	if request.method == "POST":

		form = ProductConfigurationForm(request.POST)

		if request.POST.get('delete',False):

			if form.is_valid():

				try:



					ProductConfiguration.objects.get(product=form.cleaned_data["product"],diary=form.cleaned_data["diary"]).delete()

					sale=ActualSale.objects.filter(product=form.cleaned_data["product"],
										   diary=form.cleaned_data["diary"])
					stockin=ActualStockin.objects.filter(product=form.cleaned_data["product"],
											  diary=form.cleaned_data["diary"])
					stockout=ActualStockin.objects.filter(product=form.cleaned_data["product"],
											  from_diary=form.cleaned_data["diary"])
					if sale.count()>0:
						ActualSale.objects.get(product=form.cleaned_data["product"],
											   diary=form.cleaned_data["diary"]).delete()
					if stockin.count()>0:
						ActualStockin.objects.get(product=form.cleaned_data["product"],
											  diary=form.cleaned_data["diary"]).delete()
					if stockout.count()>0:
						ActualStockin.objects.get(product=form.cleaned_data["product"],
													 from_diary=form.cleaned_data["diary"]).delete()

					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect(productConfiguration)

		if form.is_valid():

			data = form.cleaned_data
			"""print data
			obj, created = ProductConfiguration.objects.update_or_create(
					diary=data['diary'],
					defaults={'product':data['product']},

				)"""

			#product_configuration=form.save(commit=False)

			try:
				product_configuration=ProductConfiguration(diary=data['diary'],product=data['product'])
				product_configuration.save()
			except Exception as e:
				messages.info(request, "Already Exist")


			return redirect(productConfiguration)

	else:
		form=ProductConfigurationForm()
	return render(request,'prediction/ProductConfiguration.html',{'form':form,'productConfigurationList':productConfigurationList})


@login_required
@user_passes_test(group_check_diary)
def actualYearEntry(request):
	diary=diary_of_user(request.user)
	ActualWMProcurementList=ActualWMProcurement.objects.filter(diary=diary).order_by('month')
	ActualSaleList=ActualSale.objects.filter(diary=diary).order_by('month')
	ActualStockinList=ActualStockin.objects.filter(diary=diary).order_by('month')
	ActualStockoutList=ActualStockin.objects.filter(from_diary=diary).order_by('month')
	if request.method == "POST":

		form = ActualWMProcurementForm(request.POST)

		if request.POST.get('delete',False):

			if form.is_valid():

				try:
					ActualWMProcurement.objects.get(diary=diary,month=form.cleaned_data["month"]).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualyearentry/#actualwmprocurement")

		if form.is_valid():
			data = form.cleaned_data

			obj, created = ActualWMProcurement.objects.update_or_create(
					diary=diary,month=data['month'],
					defaults={'procurement':data['procurement']},

				)
			return redirect("/actualyearentry/#actualwmprocurement")

		form_sale = ActualSaleForm(request.POST)
		if request.POST.get('delete_sale',False):

			if form_sale.is_valid():

				try:
					ActualSale.objects.get(diary=diary,month=form_sale.cleaned_data["month"],product=form_sale.cleaned_data["product"]).delete()
					messages.info(request, "Successfully Deleted")
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(diary, form_sale.cleaned_data['month'],
					# 				 form_sale.cleaned_data["product"].category))
					# t.start()
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualyearentry/#actualsale")
		if form_sale.is_valid():

			data = form_sale.cleaned_data

			obj, created = ActualSale.objects.update_or_create(
					diary=diary,month=data['month'],product=data["product"],
					defaults={'sales':data['sales']},

				)
			# t = Thread(target=totalIssueRequirementDB,
			# 		   args=(diary, data['month'],
			# 				 data["product"].category))
			# t.start()
			return redirect("/actualyearentry/#actualsale")



		form_stockin=ActualStockinForm(request.POST)
		if request.POST.get('delete_stockin',False):

			if form_stockin.is_valid():

				try:
					ActualStockin.objects.get(diary=diary,from_diary=form_stockin.cleaned_data["from_diary"],month=form_stockin.cleaned_data["month"],product=form_stockin.cleaned_data["product"]).delete()
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(diary, form_stockin.cleaned_data['month'],
					# 				 form_stockin.cleaned_data["product"].category))
					# t.start()
					# t.join()
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(form_stockin.cleaned_data['from_diary'], form_stockin.cleaned_data['month'],
					# 				 form_stockin.cleaned_data["product"].category))
					# t.start()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualyearentry/#actualstockin")
		if form_stockin.is_valid():
			data = form_stockin.cleaned_data
			product_config_check=ProductConfiguration.objects.filter(diary=data['from_diary'],product=data["product"])


			if product_config_check.count()>0:

				obj, created = ActualStockin.objects.update_or_create(
					diary=diary,from_diary=data['from_diary'],month=data['month'],product=data["product"],
					defaults={'quantity':data['quantity']},

				)
				# t = Thread(target=totalIssueRequirementDB,
				# 		   args=(diary, data['month'],
				# 				 data["product"].category))
				# t.start()
				# t.join()
				# t = Thread(target=totalIssueRequirementDB,
				# 		   args=(data['from_diary'], data['month'],
				# 				 data["product"].category))
				# t.start()
			else:
				messages.info(request,"Save failed:Product not Configured in From Diary")
			return redirect("/actualyearentry/#actualstockin")

		"""if form.is_valid():
			actual_wm_procurement=form.save(commit=False)
			actual_wm_procurement.diary=diary
			actual_wm_procurement.save()

		if form_sale.is_valid():
			actual_sale=form_sale.save(commit=False)
			actual_sale.diary=diary
			actual_sale.save()

		if form_stockin.is_valid():
			actual_stock_in=form_stockin.save(commit=False)
			actual_stock_in.diary=diary
			actual_stock_in.save()
		return redirect(actualYearEntry)"""

	else:
		form=ActualWMProcurementForm()
		form_sale = ActualSaleForm()
		form_sale.fields['product'].queryset=Product.objects.filter(code__in=(ProductConfiguration.objects.filter(diary=diary).values('product'))).all()

		form_stockin=ActualStockinForm()
		form_stockin.fields['product'].queryset=Product.objects.filter(code__in=(ProductConfiguration.objects.filter(diary=diary).values('product'))).all()
	return render(request,'prediction/ActualYearEntry.html',{'form':form,'ActualWMProcurementList':ActualWMProcurementList,'form_sale':form_sale,'ActualSaleList':ActualSaleList,'form_stockin':form_stockin,'ActualStockinList':ActualStockinList,'ActualStockoutList':ActualStockoutList})

@login_required
@user_passes_test(group_check_union)
def actualYearEntryUnion(request):


	ActualWMProcurementList=ActualWMProcurement.objects.all().order_by('month')
	ActualSaleList=ActualSale.objects.all().order_by('month')
	ActualStockinList=ActualStockin.objects.all().order_by('month')
	ActualStockoutList=ActualStockin.objects.all().order_by('month')
	if request.method == "POST":
		form = ActualWMProcurementFormUnion(request.POST)

		if request.POST.get('delete',False):

			if form.is_valid():

				try:
					ActualWMProcurement.objects.get(diary=form.cleaned_data["diary"],month=form.cleaned_data["month"]).delete()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualYearEntryUnion/#actualwmprocurement")

		if form.is_valid():
			data = form.cleaned_data
			obj, created = ActualWMProcurement.objects.update_or_create(
					diary=data["diary"],month=data['month'],
					defaults={'procurement':data['procurement']},

				)

			return redirect("/actualYearEntryUnion/#actualwmprocurement")

		form_sale = ActualSaleFormUnion(request.POST)
		if request.POST.get('delete_sale',False):

			if form_sale.is_valid():

				try:
					ActualSale.objects.get(diary=form_sale.cleaned_data["diary"],month=form_sale.cleaned_data["month"],product=form_sale.cleaned_data["product"]).delete()
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(form_sale.cleaned_data["diary"], form_sale.cleaned_data["month"], form_sale.cleaned_data["product"].category))
					# t.start()
					messages.info(request, "Successfully Deleted")
				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualYearEntryUnion/#actualsale")
		if form_sale.is_valid():

			data = form_sale.cleaned_data
			obj, created = ActualSale.objects.update_or_create(
					diary=data['diary'],month=data['month'],product=data["product"],
					defaults={'sales':data['sales']},

				)
			# t = Thread(target=totalIssueRequirementDB, args=(data['diary'],data['month'],data["product"].category))
			# t.start()
			return redirect("/actualYearEntryUnion/#actualsale")



		form_stockin=ActualStockinFormUnion(request.POST)
		if request.POST.get('delete_stockin',False):

			if form_stockin.is_valid():

				try:
					ActualStockin.objects.get(diary=form_stockin.cleaned_data["diary"],from_diary=form_stockin.cleaned_data["from_diary"],month=form_stockin.cleaned_data["month"],product=form_stockin.cleaned_data["product"]).delete()
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(form_stockin.cleaned_data['diary'], form_stockin.cleaned_data['month'], form_stockin.cleaned_data["product"].category))
					# t.start()
					# t.join()
					# t = Thread(target=totalIssueRequirementDB,
					# 		   args=(form_stockin.cleaned_data['from_diary'], form_stockin.cleaned_data['month'], form_stockin.cleaned_data["product"].category))
					# t.start()
					messages.info(request, "Successfully Deleted")

				except Exception as e:
					messages.info(request, "Deletion Failed:Not Exist")

			return redirect("/actualYearEntryUnion/#actualstockin")
		if form_stockin.is_valid():
			data = form_stockin.cleaned_data
			obj, created = ActualStockin.objects.update_or_create(
					diary=data['diary'],from_diary=data['from_diary'],month=data['month'],product=data["product"],
					defaults={'quantity':data['quantity']},

				)
			# t = Thread(target=totalIssueRequirementDB, args=(data['diary'], data['month'], data["product"].category))
			# t.start()
			# t.join()
			# t = Thread(target=totalIssueRequirementDB, args=(data['from_diary'], data['month'], data["product"].category))
			# t.start()
			return redirect("/actualYearEntryUnion/#actualstockin")

		"""
		form = ActualWMProcurementFormUnion(request.POST)
		form_sale = ActualSaleFormUnion(request.POST)
		form_stockin=ActualStockinFormUnion(request.POST)
		if form.is_valid():
			actual_wm_procurement=form.save(commit=False)
			actual_wm_procurement.save()


		if form_sale.is_valid():
			actual_sale=form_sale.save(commit=False)
			actual_sale.save()

		if form_stockin.is_valid():
			actual_stock_in=form_stockin.save(commit=False)
			actual_stock_in.save()
		return redirect(actualYearEntryUnion)"""

	else:
		form=ActualWMProcurementFormUnion()
		form_sale = ActualSaleFormUnion()
		form_stockin=ActualStockinFormUnion()
	return render(request,'prediction/ActualYearEntryUnion.html',{'form':form,'ActualWMProcurementList':ActualWMProcurementList,'form_sale':form_sale,'ActualSaleList':ActualSaleList,'form_stockin':form_stockin,'ActualStockinList':ActualStockinList,'ActualStockoutList':ActualStockoutList})




@login_required
def home(request):

	if request.user.groups.filter(name="Diary").exists():
		return redirect(targetYear)
	else:
		return redirect(targetYearUnion)


@login_required
@user_passes_test(group_check_diary)
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
				#return HttpResponse("User Not Linked With Diary")
				messages.info(request, "User Not Linked With Diary")

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
					#return HttpResponse("Netvalue is zero(Stockout+Sale-Stockin=0) for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
					messages.info(request, "Netvalue is zero(Stockout+Sale-Stockin=0) for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
				print "target-",target_unit


				#changed by adding specific gravity in Quantity functions in model
				# specific_gravity=category.specific_gravity

				# target_unit_in_gram=target_unit*specific_gravity



				target_unit_in_gram = target_unit
				# ---------------

				print "target_unit_in_gram",target_unit_in_gram

				method_list=category.distinctMethodList







				if len(method_list)==0:
					#return HttpResponse("No production methods are available for this category:"+str(category.name)+" ,Please Enter Values in Composition ")
					messages.info(request, "No production methods are available for this category:"+str(category.name)+" ,Please Enter Values in Composition ")

				else:
					resultitem=[]
					result=[]
					total={}
					for method in method_list:
						print "method+",method['method']


						methodPercentage=getMethodPercentage(category,method['method'])
						if methodPercentage==0:
							#return HttpResponse("Please Verify your MethodPercentage")

							messages.info(request,"Please Verify your MethodPercentage")
						print "Method Percentage:",methodPercentage


						portion_of_target_unit_in_gram_through_this_method=target_unit_in_gram*(methodPercentage/100)


						issues=[]
						resultitem={"method":method,"portion_through_the_method":portion_of_target_unit_in_gram_through_this_method,"method_percentage":methodPercentage,"issue_required":issues}

						composition_list=Composition.objects.filter(category=category,method=method['method'])

						for composition in composition_list:
							issues=[composition.issue.name,portion_of_target_unit_in_gram_through_this_method*composition.ratio]

							if total.has_key(issues[0]):
								new_composition_value=total[issues[0]]+issues[1]
								total[issues[0]]=new_composition_value

							else:
								total[issues[0]]=issues[1]

							resultitem["issue_required"].append(issues)
						result.append(resultitem)
						print total

					if len(method_list)<=1:
						result=[]


					return render(request, "prediction/RawmaterialWise.html", {'result':result,'form':form,'total':total,'target_unit':target_unit})
			else:
				#return HttpResponse("You have not configured any product for category:"+category.name)
				messages.info(request,"You have not configured any product for category:"+category.name)
	else:
		form = CategoryWiseRequirementForm()
	return render(request, 'prediction/RawmaterialWise.html', {'form': form})


@login_required
@user_passes_test(group_check_union)
def rawmaterialWiseUnion(request):

	if request.method == "POST":

		form_union = CategoryWiseRequirementFormUnion(request.POST)

		if form_union.is_valid():

			sale_details=[]
			composdetails=[]
			compos2details=[]
			category=form_union.cleaned_data["category"]
			category_name=category.name
			month=form_union.cleaned_data["month"]


			diary=form_union.cleaned_data["diary"]

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
					#return HttpResponse("Netvalue is zero(Stockout+Sale-Stockin=0) for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
					messages.info(request, "Netvalue is zero(Stockout+Sale-Stockin=0) for "+str(category.name)+" in "+str(MONTHS[month])+" for Diary :"+str(diary.name))
				print "target-",target_unit

				# specific_gravity=category.specific_gravity
				# target_unit_in_gram=target_unit*specific_gravity
				target_unit_in_gram=target_unit


				print "target_unit_in_gram",target_unit_in_gram

				method_list=category.distinctMethodList







				if len(method_list)==0:
					#return HttpResponse("No production methods are available for this category:"+str(category.name)+" ,Please Enter Values in Composition ")
					messages.info(request, "No production methods are available for this category:"+str(category.name)+" ,Please Enter Values in Composition ")

				else:
					resultitem=[]
					result=[]
					total={}
					for method in method_list:
						print "method+",method['method']


						methodPercentage=getMethodPercentage(category,method['method'])
						if methodPercentage==0:
							#return HttpResponse("Please Verify your MethodPercentage")

							messages.info(request,"Please Verify your MethodPercentage")
						print "Method Percentage:",methodPercentage


						portion_of_target_unit_in_gram_through_this_method=target_unit_in_gram*(methodPercentage/100)
						issues=[]
						resultitem={"method":method,"portion_through_the_method":portion_of_target_unit_in_gram_through_this_method,"method_percentage":methodPercentage,"issue_required":issues}

						composition_list=Composition.objects.filter(category=category,method=method['method'])

						for composition in composition_list:
							issues=[composition.issue.name,portion_of_target_unit_in_gram_through_this_method*composition.ratio]
							if total.has_key(issues[0]):
								new_composition_value=total[issues[0]]+issues[1]
								total[issues[0]]=new_composition_value

							else:
								total[issues[0]]=issues[1]

							resultitem["issue_required"].append(issues)
						result.append(resultitem)
						print total

					if len(method_list)<=1:
						result=[]


					return render(request, "prediction/RawmaterialWiseUnion.html", {'result':result,'form':form_union,'total':total})
			else:
				#return HttpResponse("You have not configured any product for category:"+category.name)
				messages.info(request,"You have not configured any product for category:"+category.name)
	else:

		form_union = CategoryWiseRequirementFormUnion()
	return render(request, 'prediction/RawmaterialWiseUnion.html', {'form': form_union})

@login_required
@user_passes_test(group_check_union)
def issuerequirementUnion(request):

	if request.method == "POST":
		form = IssueRequirementFormUnion(request.POST)
		if form.is_valid():
			#diary = form.save(commit=False)
			#diary.save()

			issue=form.cleaned_data["issue"]
			#month=form.cleaned_data["month"]

			diary=form.cleaned_data["dairy"]

			#CategoryList=Category.objects.all()
			issue_requirement=0
			#changed for ordering the month

			# issue_monthwise={}
			issue_monthwise=OrderedDict()
			issue_as_product = OrderedDict()
			issue_as_issue = OrderedDict()
			# issue_as_product={}
			# issue_as_issue={}

			#
			#global requested_issue
			for month in MONTHS.items():

				# print "first"+str(month[1])
				ret_month,month_issue_requirement=totalIssueRequirement(month[0],diary,issue)
				issue_monthwise[ret_month]=month_issue_requirement

				ret_issueasproduct_month,issue_as_product_requirement=IssueasProduct(month[0],diary,issue)

				issue_as_product[ret_issueasproduct_month]=issue_as_product_requirement

				issue_as_issue[month[1]]=month_issue_requirement-issue_as_product_requirement


				#issue_requirement=totalIssueRequirement(month[0],diary,issue)
				"""for category in CategoryList:
					print category.name
					issue_requirement+=totalIssueRequirement(category,month[0],diary,issue)
					saledetails=ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month[0],diary=diary)

					stockindetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month[0],diary=diary)

					stockoutdetail=ActualStockin.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),month=month[0],from_diary=diary)

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
						print "\tstockout-"+str(stock.targetStockOutQuantity)
						stockout+=stock.targetStockOutQuantity

					print "\tsales",salesum
					print "\tstockout",stockout
					print "\tstockin",stockin
					target=(salesum+stockout-(stockin))
					print "\tRequired issue  "+issue.name
					requested_issue=issue
					print "\tTarget",target
					issue_requirement+=requireIssue(category,target)


					print "issue_requirement",issue_requirement"""
				#issue_monthwise.append({month[1]:issue_requirement})


				# print str(issue_monthwise)+str(month[1])
			return render(request, "prediction/IssueWiseUnion.html",{"issue_monthwise":issue_monthwise,'form':form,'issue_as_product':issue_as_product,'issue_as_issue':issue_as_issue})

	else:
		form = IssueRequirementFormUnion()
	#return render(request, 'prediction/issue_requirement.html', {'form': form})
	return render(request, 'prediction/IssueWiseUnion.html', {'form': form})


@login_required
@user_passes_test(group_check_union)
def interStockMilkTransferUnion(request):

	if request.method == "POST":
		form = MonthOnlyForm(request.POST)

		if form.is_valid():

			issue = Issue.objects.get(name='WM')

			month = form.cleaned_data["month"]




			resultitem = []

			shortage_list=OrderedDict()
			surplus_list=OrderedDict()


			fwm = issue.fat

			diary_list = Diary.objects.all()
			total_requirement_diary_cpd = 0
			for diary in diary_list:

				try:

					month_issue_requirement_sales = IssueRequirement.objects.get(month=month, diary=diary,
																		   issue=issue).requirement


				except Exception as e:
					month_issue_requirement_sales = 0



				month_requirement_for_milk_issue_production = 0
				type2_issue_list = Issue.objects.filter(type='2')
				for issue_item in type2_issue_list:

					# issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)

					try:

						month_issue_requirement = IssueRequirement.objects.get(month=month, diary=diary,
																			   issue=issue_item).requirement


					except Exception as e:
						month_issue_requirement = 0

					composition_ratio_derived = 0
					if  issue.name == "WM":
						try:
							if issue_item.fat > fwm:
								composition_ratio_derived = qwmValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))
							else:
								composition_ratio_derived = qwmValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))
						except Exception as e:
							print "Exception handled in line no 1484"

					requirement_to_produce_milk_issue = month_issue_requirement * composition_ratio_derived
					month_requirement_for_milk_issue_production += requirement_to_produce_milk_issue

				total_month_requirement = month_requirement_for_milk_issue_production + month_issue_requirement_sales
				# total_month_requirement = month_requirement_for_milk_issue_production
				total_month_procurement=0
				try:
					Awm_obj=ActualWMProcurement.objects.get(diary=diary, month=month)
					total_month_procurement = Awm_obj.targetProcurement
				except Exception as e:
					print "Exception handled in line 1492"

				difference=total_month_procurement-total_month_requirement
				if difference !=0:
					type_of_difference=""
					if difference>=0:
						type_of_difference="Surplus"
						surplus_list[diary.name]=difference
					else:
						type_of_difference="Shortage"
						difference=difference*-1
						shortage_list[diary.name]=difference

					result = {"month":MONTHS[month],"diary":diary.name,"requirement":total_month_requirement,"procurement":total_month_procurement,"difference":difference,"type":type_of_difference}
					resultitem.append(result)

				if "CPD"==diary.id:
					total_requirement_diary_cpd=total_month_requirement



			# print str(shortage_list)
			# print str(surplus_list)

			after_transfer_value,inter_stock_transfer=interMilkTransfer(shortage_list,surplus_list,total_requirement_diary_cpd,diary_list)

			if after_transfer_value<0:
				after_transfer ="Shortage"
				after_transfer_value*=(-1)


				purchase_rate=GeneralCalculation.objects.get(code=8).value
				wm_after_stock_transfer="WM Purchased:"+str('{0:.4f}'.format(after_transfer_value))+", Amount:"+str('{0:.4f}'.format(after_transfer_value*purchase_rate))


				max_allowable_reconstitution=GeneralCalculation.objects.get(code=1).value
			else:
				after_transfer = "Surplus"

				sale_percentage=GeneralCalculation.objects.get(code=4).value
				sale_rate=GeneralCalculation.objects.get(code=9).value
				wm_after_stock_transfer="WM Sold:"+str('{0:.4f}'.format(after_transfer_value*sale_percentage/100))+", Amount:"+str('{0:.4f}'.format(after_transfer_value*sale_rate))


				csm_convert_percentage=GeneralCalculation.objects.get(code=5).value
				wm_converted_to_csm=after_transfer_value*csm_convert_percentage/100


				csm_sale_percentage= GeneralCalculation.objects.get(code=6).value
				csm_sale_rate=GeneralCalculation.objects.get(code=10).value
				csm_sold=wm_converted_to_csm*csm_sale_percentage/100
				csm_sold_amount=csm_sold*csm_sale_rate


				csm_smp_conversion_percentage=GeneralCalculation.objects.get(code=7).value
				csm_converted_to_smp=wm_converted_to_csm*csm_smp_conversion_percentage/100








			return render(request, 'prediction/InterStockMilkTransferUnion.html', {'form': form,'resultitem': resultitem,'interstock':inter_stock_transfer,'after_transfer_value':after_transfer_value,'after_transfer':after_transfer,'wm_after_stock_transfer':wm_after_stock_transfer})
	else:
		form = MonthOnlyForm()
		return render(request, 'prediction/InterStockMilkTransferUnion.html', {'form': form})

@login_required
@user_passes_test(group_check_diary)
def balancing(request):
	if request.method == "POST":
		form = MonthOnlyForm(request.POST)
		if form.is_valid():

			issue_wm = Issue.objects.get(name='WM')


			issue_cream=Issue.objects.get(name='CREAM')
			issue_smp = Issue.objects.get(name='SMP')

			month = form.cleaned_data["month"]




			resultitem = []

			cream_requirement_list=[]

			smp_requirement_list = []

			wmp_requirement_list=[]
			shortage_list=OrderedDict()
			surplus_list=OrderedDict()


			fwm = issue_wm.fat

			diary_list = Diary.objects.all()
			total_requirement_diary_cpd = 0
			for diary in diary_list:



				ret_month,month_issue_requirement_sales_wm = totalIssueRequirement(month, diary, issue_wm)

				ret_month, month_issue_requirement_sales_cream = totalIssueRequirement(month, diary, issue_cream)

				ret_month, month_issue_requirement_sales_smp = totalIssueRequirement(month, diary, issue_smp)


				month_requirement_for_milk_issue_production_wm = 0
				month_requirement_for_milk_issue_production_cream = 0
				month_requirement_for_milk_issue_production_smp = 0
				type2_issue_list = Issue.objects.filter(type='2')

				for issue_item in type2_issue_list:

					# issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)

					try:

						issue_ret_month,month_issue_requirement =totalIssueRequirement(month, diary, issue_item)


					except Exception as e:
						month_issue_requirement = 0

					composition_ratio_derived_wm = 0

					try:
						if issue_item.fat > fwm:
							composition_ratio_derived_wm = qwmValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

							composition_ratio_derived_cream = qcValue(issue_item) / (
								qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

							composition_ratio_derived_smp = qsmpValue(issue_item) / (
							qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

						else:
							composition_ratio_derived_wm = qwmValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))

							composition_ratio_derived_cream = -1 * (qcValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item)))
							composition_ratio_derived_smp = qsmpValue(issue_item) / (
								(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))

					except Exception as e:
						print "Exception handled in line no 1484"

					requirement_to_produce_milk_issue_wm = month_issue_requirement * composition_ratio_derived_wm
					month_requirement_for_milk_issue_production_wm += requirement_to_produce_milk_issue_wm

					requirement_to_produce_milk_issue_cream = month_issue_requirement * composition_ratio_derived_cream
					month_requirement_for_milk_issue_production_cream += requirement_to_produce_milk_issue_cream

					requirement_to_produce_milk_issue_smp = month_issue_requirement * composition_ratio_derived_smp
					month_requirement_for_milk_issue_production_smp += requirement_to_produce_milk_issue_smp


				total_month_requirement_wm = month_requirement_for_milk_issue_production_wm + month_issue_requirement_sales_wm

				total_month_requirement_cream=month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_cream

				total_month_requirement_smp = month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_smp

				# total_month_requirement = month_requirement_for_milk_issue_production
				total_month_procurement=0
				try:
					Awm_obj=ActualWMProcurement.objects.get(diary=diary, month=month)
					total_month_procurement = Awm_obj.targetProcurement
				except Exception as e:
					print "Exception handled in line 1749"

				difference=total_month_procurement-total_month_requirement_wm



				if difference !=0:
					type_of_difference=""
					if difference>=0:
						type_of_difference="Surplus"
						surplus_list[diary.name]=difference
					else:
						type_of_difference="Shortage"
						difference=difference*-1
						shortage_list[diary.name]=difference

					result = {"month":MONTHS[month],"diary":diary.name,"requirement":total_month_requirement_wm,"procurement":total_month_procurement,"difference":difference,"type":type_of_difference}
					resultitem.append(result)

				if "CPD"==diary.id:
					total_requirement_diary_cpd=total_month_requirement_wm




				cream_requirement_item={"month":MONTHS[month],"diary":diary,"total_cream_used":0-total_month_requirement_cream,"type":"Surplus"}
				cream_requirement_list.append(cream_requirement_item)
				smp_requirement_item = {"month": MONTHS[month], "diary": diary,
									  "total_smp_used": 0 - total_month_requirement_smp, "type": "Sale"}
				smp_requirement_list.append(smp_requirement_item)

				wmp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_wmp_used": 0 , "type": "Sale"}
				wmp_requirement_list.append(wmp_requirement_item)



			# print str(shortage_list)
			print str(cream_requirement_list)
			diary = diary_of_user(request.user)
			after_transfer_diary,inter_stock_transfer=interMilkTransfer(shortage_list,surplus_list,total_requirement_diary_cpd,diary_list)
			after_wm_balancing_diarylist=wmBalancing(after_transfer_diary,month)

			wm_after_transfer=[]

			shortage_list_cream = OrderedDict()
			surplus_list_cream = OrderedDict()

			cream_list=[]
			for item_cream in cream_requirement_list:



				for item in after_wm_balancing_diarylist:
					if item['diary']==diary.name:
						wm_after_transfer.append(item)





					if item_cream['diary'].name==item['diary']:


						requirement=item_cream['total_cream_used']*(-1)
						item_cream['total_cream_used']=0-(requirement+item['cream_used_csm']+item['cream_used_smp'])



					if item_cream['total_cream_used'] < 0:
						item_cream['type'] = "Shortage"

						cream_used=item_cream['total_cream_used'] * (-1)
						shortage_list_cream[item_cream['diary']]=cream_used*(-1)


					elif item_cream['total_cream_used']>0:
						item_cream['type'] = "Surplus"
						surplus_list_cream[item_cream['diary']] = item_cream['total_cream_used']
				if item_cream['total_cream_used']!=0:
					if item_cream['total_cream_used']<0:
						item_cream['total_cream_used']=item_cream['total_cream_used']*(-1)
					cream_list.append(item_cream)
			smp_after_transfer=[]
			for item_smp in smp_requirement_list:

				for item in after_wm_balancing_diarylist:
					if item_smp['diary'].name == item['diary']:
						requirement = item_smp['total_smp_used'] * (-1)
						item_smp['total_smp_used'] = 0 - (requirement + item['smp_used_smp'] + item['smp_used_wmp']-item['converted_smp'])

					if item_smp['total_smp_used'] < 0:
						item_smp['type'] = "Purchase"

						used = item_smp['total_smp_used'] * (-1)

						item_smp['total_smp_used'] = used

					elif item_smp['total_smp_used'] > 0:
						item_smp['type'] = "Sale"
				if item_smp['diary'].name == diary.name:

					if item_smp['type']=="Sale":
						try:
							sale_rate=GeneralCalculation.objects.get(code='14').value
							smp_item={'transaction':'SMP Sold:'+str('{0:.4f}'.format(item_smp['total_smp_used']))+" ,Amount:"+str('{0:.4f}'.format(item_smp['total_smp_used']*sale_rate))}

						except Exception as e:
							print "Exception handled At 2034"
					else:
						try:
							rate = GeneralCalculation.objects.get(code='13').value
							smp_item = {'transaction': 'SMP Purchased:' + str(
								'{0:.4f}'.format(item_smp['total_smp_used'])) + " ,Amount:" + str(
								'{0:.4f}'.format(item_smp['total_smp_used'] * rate))}

						except Exception as e:
							print "Exception handled At 2045"

					smp_after_transfer.append(smp_item)
			wmp_after_transfer=[]
			for item_wmp in wmp_requirement_list:

				for item in after_wm_balancing_diarylist:
					if item_wmp['diary'].name == item['diary']:

						item_wmp['total_wmp_used'] = 0 - item['wmp_used']
						if item_wmp['total_wmp_used'] < 0:
							item_wmp['type'] = "Purchase"

							used = item_wmp['total_wmp_used'] * (-1)

							item_wmp['total_wmp_used'] = used

						elif item_wmp['total_wmp_used'] > 0:
							item_wmp['type'] = "Sale"
				if item_wmp['diary'].name == diary.name:

					if item_wmp['type'] == "Sale":
						try:
							sale_rate = GeneralCalculation.objects.get(code='12').value
							wmp_item = {'transaction': 'WMP Sold:' + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'])) + " ,Amount:" + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'] * sale_rate))}

						except Exception as e:
							print "Exception handled At 2078"
					else:
						try:
							rate = GeneralCalculation.objects.get(code='11').value
							wmp_item = {'transaction': 'WMP Purchased:' + str(
								'{0:.4f}'.format(item_wmp['total_wmp_used'])) + " ,Amount:" + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'] * rate))}

						except Exception as e:
							print "Exception handled At 2087"

					wmp_after_transfer.append(wmp_item)

			after_cream_transfer_diary, inter_stock_transfer_cream = interCreamTransfer(shortage_list_cream, surplus_list_cream,
																		    diary_list)


			after_cream_balancing_diarylist = creamBalancing(after_cream_transfer_diary)

			cream_after_transfer=[]



			for item in after_cream_balancing_diarylist:
				if item['diary'].name == diary.name:
					cream_after_transfer.append(item)

			if not bool(wm_after_transfer):
				transaction_item = {'after_transfer': 'Balanced'}
				wm_after_transfer.append(transaction_item)

			return render(request, 'prediction/Balancing.html',
						  {'form': form, 'resultitem': resultitem, 'interstock': inter_stock_transfer,'after_transfer': wm_after_transfer

						   ,'cream_list':cream_list,'inter_stock_cream':inter_stock_transfer_cream,'cream_after_transfer': cream_after_transfer
						   ,'smp_list':smp_requirement_list,'smp_after_transfer':smp_after_transfer,'wmp_list':wmp_requirement_list,'wmp_after_transfer':wmp_after_transfer})

						   # 'after_transfer_value': after_transfer_value, 'after_transfer': after_transfer,
						   # 'wm_after_stock_transfer': wm_after_stock_transfer
	else:
		form = MonthOnlyForm()
		return render(request, 'prediction/Balancing.html', {'form': form})


@login_required
@user_passes_test(group_check_union)
def balancingUnion(request):
	if request.method == "POST":
		form = MonthOnlyForm(request.POST)
		if form.is_valid():

			issue_wm = Issue.objects.get(name='WM')


			issue_cream=Issue.objects.get(name='CREAM')
			issue_smp = Issue.objects.get(name='SMP')

			month = form.cleaned_data["month"]




			resultitem = []

			cream_requirement_list=[]

			smp_requirement_list = []

			wmp_requirement_list=[]
			shortage_list=OrderedDict()
			surplus_list=OrderedDict()


			fwm = issue_wm.fat

			diary_list = Diary.objects.all()
			total_requirement_diary_cpd = 0
			for diary in diary_list:



				ret_month,month_issue_requirement_sales_wm = totalIssueRequirement(month, diary, issue_wm)

				ret_month, month_issue_requirement_sales_cream = totalIssueRequirement(month, diary, issue_cream)

				ret_month, month_issue_requirement_sales_smp = totalIssueRequirement(month, diary, issue_smp)


				month_requirement_for_milk_issue_production_wm = 0
				month_requirement_for_milk_issue_production_cream = 0
				month_requirement_for_milk_issue_production_smp = 0
				type2_issue_list = Issue.objects.filter(type='2')

				for issue_item in type2_issue_list:

					# issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)

					try:

						issue_ret_month,month_issue_requirement =totalIssueRequirement(month, diary, issue_item)


					except Exception as e:
						month_issue_requirement = 0

					composition_ratio_derived_wm = 0

					try:
						if issue_item.fat > fwm:
							composition_ratio_derived_wm = qwmValue(issue_item) / (
									qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

							composition_ratio_derived_cream = qcValue(issue_item) / (
								qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

							composition_ratio_derived_smp = qsmpValue(issue_item) / (
							qcValue(issue_item) + qwmValue(issue_item) + qsmpValue(issue_item))

						else:
							composition_ratio_derived_wm = qwmValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))

							composition_ratio_derived_cream = -1 * (qcValue(issue_item) / (
									(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item)))
							composition_ratio_derived_smp = qsmpValue(issue_item) / (
								(qwmValue(issue_item) - qcValue(issue_item)) + qsmpValue(issue_item))

					except Exception as e:
						print "Exception handled in line no 1484"

					requirement_to_produce_milk_issue_wm = month_issue_requirement * composition_ratio_derived_wm
					month_requirement_for_milk_issue_production_wm += requirement_to_produce_milk_issue_wm

					requirement_to_produce_milk_issue_cream = month_issue_requirement * composition_ratio_derived_cream
					month_requirement_for_milk_issue_production_cream += requirement_to_produce_milk_issue_cream

					requirement_to_produce_milk_issue_smp = month_issue_requirement * composition_ratio_derived_smp
					month_requirement_for_milk_issue_production_smp += requirement_to_produce_milk_issue_smp


				total_month_requirement_wm = month_requirement_for_milk_issue_production_wm + month_issue_requirement_sales_wm

				total_month_requirement_cream=month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_cream

				total_month_requirement_smp = month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_smp

				# total_month_requirement = month_requirement_for_milk_issue_production
				total_month_procurement=0
				try:
					Awm_obj=ActualWMProcurement.objects.get(diary=diary, month=month)
					total_month_procurement = Awm_obj.targetProcurement
				except Exception as e:
					print "Exception handled in line 1749"

				difference=total_month_procurement-total_month_requirement_wm



				if difference !=0:
					type_of_difference=""
					if difference>=0:
						type_of_difference="Surplus"
						surplus_list[diary.name]=difference
					else:
						type_of_difference="Shortage"
						difference=difference*-1
						shortage_list[diary.name]=difference

					result = {"month":MONTHS[month],"diary":diary.name,"requirement":total_month_requirement_wm,"procurement":total_month_procurement,"difference":difference,"type":type_of_difference}
					resultitem.append(result)

				if "CPD"==diary.id:
					total_requirement_diary_cpd=total_month_requirement_wm




				cream_requirement_item={"month":MONTHS[month],"diary":diary,"total_cream_used":0-total_month_requirement_cream,"type":"Surplus"}
				cream_requirement_list.append(cream_requirement_item)
				smp_requirement_item = {"month": MONTHS[month], "diary": diary,
									  "total_smp_used": 0 - total_month_requirement_smp, "type": "Sale"}
				smp_requirement_list.append(smp_requirement_item)

				wmp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_wmp_used": 0 , "type": "Sale"}
				wmp_requirement_list.append(wmp_requirement_item)



			# print str(shortage_list)


			after_transfer_diary,inter_stock_transfer=interMilkTransfer(shortage_list,surplus_list,total_requirement_diary_cpd,diary_list)
			after_wm_balancing_diarylist=wmBalancing(after_transfer_diary,month)



			shortage_list_cream = OrderedDict()
			surplus_list_cream = OrderedDict()

			cream_list=[]
			for item_cream in cream_requirement_list:



				for item in after_wm_balancing_diarylist:






					if item_cream['diary'].name==item['diary']:


						requirement=item_cream['total_cream_used']*(-1)
						item_cream['total_cream_used']=0-(requirement+item['cream_used_csm']+item['cream_used_smp'])



					if item_cream['total_cream_used'] < 0:
						item_cream['type'] = "Shortage"

						cream_used=item_cream['total_cream_used'] * (-1)
						shortage_list_cream[item_cream['diary']]=cream_used*(-1)


					elif item_cream['total_cream_used']>0:
						item_cream['type'] = "Surplus"
						surplus_list_cream[item_cream['diary']] = item_cream['total_cream_used']
				if item_cream['total_cream_used']!=0:
					if item_cream['total_cream_used']<0:
						item_cream['total_cream_used']=item_cream['total_cream_used']*(-1)
					cream_list.append(item_cream)
			smp_after_transfer=[]
			for item_smp in smp_requirement_list:

				for item in after_wm_balancing_diarylist:
					if item_smp['diary'].name == item['diary']:
						requirement = item_smp['total_smp_used'] * (-1)
						item_smp['total_smp_used'] = 0 - (requirement + item['smp_used_smp'] + item['smp_used_wmp']-item['converted_smp'])


					if item_smp['total_smp_used'] < 0:
						item_smp['type'] = "Purchase"

						used = item_smp['total_smp_used'] * (-1)

						item_smp['total_smp_used'] = used

					elif item_smp['total_smp_used'] > 0:
						item_smp['type'] = "Sale"


				if item_smp['type']=="Sale":
					try:
						sale_rate=GeneralCalculation.objects.get(code='14').value
						smp_item={'transaction':'SMP Sold:'+str('{0:.4f}'.format(item_smp['total_smp_used']))+" ,Amount:"+str('{0:.4f}'.format(item_smp['total_smp_used']*sale_rate)),'diary':item_smp['diary'].name}

					except Exception as e:
						print "Exception handled At 2034"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='13').value
						smp_item = {'transaction': 'SMP Purchased:' + str(
								'{0:.4f}'.format(item_smp['total_smp_used'])) + " ,Amount:" + str(
								'{0:.4f}'.format(item_smp['total_smp_used'] * rate)),'diary':item_smp['diary'].name}


					except Exception as e:
						print "Exception handled At 2045"
				if item_smp['total_smp_used'] != 0:
					smp_after_transfer.append(smp_item)
			wmp_after_transfer=[]
			for item_wmp in wmp_requirement_list:

				for item in after_wm_balancing_diarylist:
					if item_wmp['diary'].name == item['diary']:

						item_wmp['total_wmp_used'] = 0 - item['wmp_used']
						if item_wmp['total_wmp_used'] < 0:
							item_wmp['type'] = "Purchase"

							used = item_wmp['total_wmp_used'] * (-1)

							item_wmp['total_wmp_used'] = used

						elif item_wmp['total_wmp_used'] > 0:
							item_wmp['type'] = "Sale"


				if item_wmp['type'] == "Sale":
					try:
						sale_rate = GeneralCalculation.objects.get(code='12').value
						wmp_item = {'transaction': 'WMP Sold:' + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'])) + " ,Amount:" + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'] * sale_rate)),'diary':item_wmp['diary'].name}

					except Exception as e:
						print "Exception handled At 2078"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='11').value
						wmp_item = {'transaction': 'WMP Purchased:' + str(
								'{0:.4f}'.format(item_wmp['total_wmp_used'])) + " ,Amount:" + str(
									'{0:.4f}'.format(item_wmp['total_wmp_used'] * rate)),'diary':item_wmp['diary'].name}

					except Exception as e:
						print "Exception handled At 2087"
				if item_wmp['total_wmp_used']!=0:
					wmp_after_transfer.append(wmp_item)

			after_cream_transfer_diary, inter_stock_transfer_cream = interCreamTransfer(shortage_list_cream, surplus_list_cream,
																		    diary_list)


			after_cream_balancing_diarylist = creamBalancing(after_cream_transfer_diary)











			return render(request, 'prediction/BalancingUnion.html',
						  {'form': form, 'resultitem': resultitem, 'interstock': inter_stock_transfer,'after_transfer': after_wm_balancing_diarylist

						   ,'cream_list':cream_list,'inter_stock_cream':inter_stock_transfer_cream,'cream_after_transfer': after_cream_balancing_diarylist
						   ,'smp_list':smp_requirement_list,'smp_after_transfer':smp_after_transfer,'wmp_list':wmp_requirement_list,'wmp_after_transfer':wmp_after_transfer})

						   # 'after_transfer_value': after_transfer_value, 'after_transfer': after_transfer,
						   # 'wm_after_stock_transfer': wm_after_stock_transfer
	else:
		form = MonthOnlyForm()
		return render(request, 'prediction/BalancingUnion.html', {'form': form})
@login_required
@user_passes_test(group_check_union)
def generalCalculation(request):
	calculationList = GeneralCalculation.objects.all().order_by('code')
	if request.method == "POST":
		form = GeneralCalculationForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data


			calculation_obj = GeneralCalculation.objects.get(code=data['calculation_Name'])
			calculation_obj.value=data['value']
			if data['calculation_Name']=='2':
				if GeneralCalculation.objects.get(code='3').value!=0 and data['value']!=0:
					if (data['value']+GeneralCalculation.objects.get(code='3').value)==100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of Reconstitution(WMP+SMP) Must Be 100")
				else:
					calculation_obj.save()
			elif data['calculation_Name']=='3':
				if data['value']!=0 and GeneralCalculation.objects.get(code='2').value!=0:
					if (data['value'] + GeneralCalculation.objects.get(code='2').value) == 100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of Reconstitution(WMP+SMP) Must Be 100")
				else:
					calculation_obj.save()

			else:
				calculation_obj.save()
			return redirect(generalCalculation)
	else:
		form = GeneralCalculationForm()
	return render(request, 'prediction/GeneralCalculation.html', {'form':form,'calculationList': calculationList})

@login_required
@user_passes_test(group_check_union)
def financialYear(request):
	current_finyear = ConfigurationAttribute.objects.first()
	if request.method == "POST":
		form = FinancialYearForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			if current_finyear:

				current_finyear.financial_Year=data['financial_Year']
				current_finyear.save()
			else:
				fin_obj = form.save(commit=False)
				fin_obj.save()

			return redirect(financialYear)
	else:
		form = FinancialYearForm()
		next_year ="-----"
		if current_finyear:


			form.fields['financial_Year'].initial = current_finyear.financial_Year
			next_year=current_finyear.financial_Year+1

	return render(request, 'prediction/FinancialYear.html', {'form': form,'next_year':next_year,'next_year_plus':next_year+1})
@login_required
@user_passes_test(group_check_union)
def wmProcurementRate(request):
	rate_obj = ConfigurationAttribute.objects.first()
	if request.method == "POST":
		form = WMProcurementRateForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			if rate_obj:

				rate_obj.wm_procurement_rate=data['wm_procurement_rate']
				rate_obj.save()
			else:
				form_obj = form.save(commit=False)
				form_obj.save()

			return redirect(wmProcurementRate)
	else:
		form = WMProcurementRateForm()

		if rate_obj:
			form.fields['wm_procurement_rate'].initial = rate_obj.wm_procurement_rate


	return render(request, 'prediction/WMProcurement.html', {'form': form})







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
