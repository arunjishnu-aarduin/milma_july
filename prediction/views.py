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
import calendar






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

				total_month_requirement_smp = month_requirement_for_milk_issue_production_smp + month_issue_requirement_sales_smp

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
							smp_item={'transaction':'SMP Sold:'+str(item_smp['total_smp_used'])+" ,Amount:"+str(item_smp['total_smp_used']*sale_rate)}

						except Exception as e:
							print "Exception handled At 2034"
					else:
						try:
							rate = GeneralCalculation.objects.get(code='13').value
							smp_item = {'transaction': 'SMP Purchased:' + str(
								item_smp['total_smp_used']) + " ,Amount:" + str(
								item_smp['total_smp_used'] * rate)}

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
									item_wmp['total_wmp_used']) + " ,Amount:" + str(
									item_wmp['total_wmp_used'] * sale_rate)}

						except Exception as e:
							print "Exception handled At 2078"
					else:
						try:
							rate = GeneralCalculation.objects.get(code='11').value
							wmp_item = {'transaction': 'WMP Purchased:' + str(
								item_wmp['total_wmp_used']) + " ,Amount:" + str(
									item_wmp['total_wmp_used'] * rate)}

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
def reportAnnual(request):


	total_milk_handled=OrderedDict()
	wm_requirement_product=OrderedDict()
	total_sm_required=OrderedDict()
	total_milk_required_products=OrderedDict()
	milk_diverted_percentage=OrderedDict()
	wm_surplus_sale=OrderedDict()
	distress_milk_percentage=OrderedDict()
	csm_surplus_sale=OrderedDict()
	csm_converted_smp=OrderedDict()
	total_cream_handled=OrderedDict()
	total_cream_matric=OrderedDict()
	total_cream_required=OrderedDict()
	total_cream_purchased=OrderedDict()
	total_cream_sold=OrderedDict()
	distress_cream_percentage=OrderedDict()
	wm_purchase_percentage=OrderedDict()
	total_smp_purchased=OrderedDict()
	total_smp_sold=OrderedDict()
	total_smp_recieved=OrderedDict()
	total_wmp_sold=OrderedDict()
	total_wmp_purchased=OrderedDict()
	category_sale_list=OrderedDict()
	month_list=OrderedDict()
	CategoryList=Category.objects.all()


	for month_item in MONTHS.items():

		issue_wm = Issue.objects.get(name='WM')

		issue_cream = Issue.objects.get(name='CREAM')
		issue_smp = Issue.objects.get(name='SMP')

		month=month_item[0]
		month_list[month] = month_item[1]






		resultitem = []

		cream_requirement_list = []

		smp_requirement_list = []

		wmp_requirement_list = []
		shortage_list = OrderedDict()
		surplus_list = OrderedDict()

		fwm = issue_wm.fat

		diary_list = Diary.objects.all()
		total_requirement_diary_cpd = 0
		wm_requirement_product_month=0
		wm_procurement_union = 0

		wm_reconstitution_union = 0
		wm_purchase_union = 0
		total_sm_union=0
		total_milk_required_union=0
		wm_surplus_sale_union=0
		csm_surplus_sale_union=0
		cream_reconstitution_union=0

		csm_converted_smp_union=0

		total_cream_required_union=0
		cream_sold_union=0
		cream_purchased_union=0
		total_smp_purchased_union=0
		total_smp_sold_union=0
		total_smp_recieved_union=0
		total_wmp_sold_union=0
		total_wmp_purchased_union=0

		for diary in diary_list:

			ret_month, month_issue_requirement_sales_wm = totalIssueRequirement(month, diary, issue_wm)

			m, issueasproduct_wm = IssueasProduct(month, diary, issue_wm)


			wm_requirement_product_month += month_issue_requirement_sales_wm-issueasproduct_wm

			ret_month, month_issue_requirement_sales_cream = totalIssueRequirement(month, diary, issue_cream)



			ret_month, month_issue_requirement_sales_smp = totalIssueRequirement(month, diary, issue_smp)




			m, issueasproduct = IssueasProduct(month, diary, issue_wm)
			total_milk_required_union+=issueasproduct

			m, issueasproduct_cream = IssueasProduct(month, diary, issue_cream)

			total_cream_required_union+=month_issue_requirement_sales_cream-issueasproduct_cream

			month_requirement_for_milk_issue_production_wm = 0
			month_requirement_for_milk_issue_production_cream = 0
			month_requirement_for_milk_issue_production_smp = 0
			type2_issue_list = Issue.objects.filter(type='2')

			for issue_item in type2_issue_list:



				try:

					issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)

					if issue_item.name=="SM":
						m,issueasproduct_sm=IssueasProduct(month,diary,issue_item)
						total_sm_union+=(month_issue_requirement-issueasproduct_sm)


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
					print "Exception handled reportAnnual in line no 2266"

				requirement_to_produce_milk_issue_wm = month_issue_requirement * composition_ratio_derived_wm
				month_requirement_for_milk_issue_production_wm += requirement_to_produce_milk_issue_wm

				requirement_to_produce_milk_issue_cream = month_issue_requirement * composition_ratio_derived_cream
				month_requirement_for_milk_issue_production_cream += requirement_to_produce_milk_issue_cream

				requirement_to_produce_milk_issue_smp = month_issue_requirement * composition_ratio_derived_smp
				month_requirement_for_milk_issue_production_smp += requirement_to_produce_milk_issue_smp

			total_month_requirement_wm = month_requirement_for_milk_issue_production_wm + month_issue_requirement_sales_wm

			total_month_requirement_cream = month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_cream

			total_month_requirement_smp = month_requirement_for_milk_issue_production_smp + month_issue_requirement_sales_smp





			total_month_procurement = 0
			try:
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)

				total_month_procurement = Awm_obj.targetProcurement
				wm_procurement_union+=total_month_procurement

			except Exception as e:
				print "Exception handled reportAnnual in line 1749"

			difference = total_month_procurement - total_month_requirement_wm

			if difference != 0:
				type_of_difference = ""
				if difference >= 0:
					type_of_difference = "Surplus"
					surplus_list[diary.name] = difference
				else:
					type_of_difference = "Shortage"
					difference = difference * -1
					shortage_list[diary.name] = difference



			if "CPD" == diary.id:
				total_requirement_diary_cpd = total_month_requirement_wm

			cream_requirement_item = {"month": MONTHS[month], "diary": diary,
									  "total_cream_used": 0 - total_month_requirement_cream, "type": "Surplus"}
			cream_requirement_list.append(cream_requirement_item)
			smp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_smp_used": 0 - total_month_requirement_smp, "type": "Sale"}
			smp_requirement_list.append(smp_requirement_item)

			wmp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_wmp_used": 0, "type": "Sale"}
			wmp_requirement_list.append(wmp_requirement_item)




		after_transfer_diary, inter_stock_transfer = interMilkTransfer(shortage_list, surplus_list,
																	   total_requirement_diary_cpd, diary_list)
		after_wm_balancing_diarylist,wm_reconstitution,wm_purchase,wm_sale,csm_sale,csm_converted,cream_reconstitution,converted_smp = wmBalancingReport(after_transfer_diary, month)

		total_smp_recieved_union+=converted_smp

		cream_reconstitution_union+=cream_reconstitution

		csm_converted_smp_union+=csm_converted

		csm_surplus_sale_union+=csm_sale

		wm_surplus_sale_union+=wm_sale

		wm_reconstitution_union+=wm_reconstitution
		wm_purchase_union+=wm_purchase

		shortage_list_cream = OrderedDict()
		surplus_list_cream = OrderedDict()

		cream_list = []
		for item_cream in cream_requirement_list:

			for item in after_wm_balancing_diarylist:

				if item_cream['diary'].name == item['diary']:
					requirement = item_cream['total_cream_used'] * (-1)
					item_cream['total_cream_used'] = 0 - (requirement + item['cream_used_csm'] + item['cream_used_smp'])

				if item_cream['total_cream_used'] < 0:
					item_cream['type'] = "Shortage"

					cream_used = item_cream['total_cream_used'] * (-1)
					shortage_list_cream[item_cream['diary']] = cream_used * (-1)


				elif item_cream['total_cream_used'] > 0:
					item_cream['type'] = "Surplus"
					surplus_list_cream[item_cream['diary']] = item_cream['total_cream_used']
			if item_cream['total_cream_used'] != 0:
				if item_cream['total_cream_used'] < 0:
					item_cream['total_cream_used'] = item_cream['total_cream_used'] * (-1)
				cream_list.append(item_cream)
		smp_after_transfer = []
		for item_smp in smp_requirement_list:

			for item in after_wm_balancing_diarylist:
				if item_smp['diary'].name == item['diary']:
					requirement = item_smp['total_smp_used'] * (-1)
					item_smp['total_smp_used'] = 0 - (
					requirement + item['smp_used_smp'] + item['smp_used_wmp'] - item['converted_smp'])

				if item_smp['total_smp_used'] < 0:
					item_smp['type'] = "Purchase"

					used = item_smp['total_smp_used'] * (-1)



					item_smp['total_smp_used'] = used

				elif item_smp['total_smp_used'] > 0:
					item_smp['type'] = "Sale"

			if item_smp['type'] == "Sale":
				try:
					sale_rate = GeneralCalculation.objects.get(code='14').value

					total_smp_sold_union+=item_smp['total_smp_used']
					smp_item = {
						'transaction': 'SMP Sold:' + str(item_smp['total_smp_used']) + " ,Amount:" + str(
							item_smp['total_smp_used'] * sale_rate), 'diary': item_smp['diary'].name}

				except Exception as e:
					print "Exception handled At 2034"
			else:
				try:
					rate = GeneralCalculation.objects.get(code='13').value
					total_wmp_purchased_union += item_smp['total_smp_used']
					total_smp_purchased_union+=item_smp['total_smp_used']
					smp_item = {'transaction': 'SMP Purchased:' + str(
						item_smp['total_smp_used']) + " ,Amount:" + str(
						item_smp['total_smp_used'] * rate), 'diary': item_smp['diary'].name}


				except Exception as e:
					print "Exception handled At 2045"
			if item_smp['total_smp_used'] != 0:
				smp_after_transfer.append(smp_item)
		wmp_after_transfer = []
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
						item_wmp['total_wmp_used']) + " ,Amount:" + str(
						item_wmp['total_wmp_used'] * sale_rate), 'diary': item_wmp['diary'].name}

				except Exception as e:
					print "Exception handled At 2078"
			else:
				try:
					rate = GeneralCalculation.objects.get(code='11').value
					wmp_item = {'transaction': 'WMP Purchased:' + str(
						item_wmp['total_wmp_used']) + " ,Amount:" + str(
						item_wmp['total_wmp_used'] * rate), 'diary': item_wmp['diary'].name}

				except Exception as e:
					print "Exception handled At 2087"
			if item_wmp['total_wmp_used'] != 0:
				wmp_after_transfer.append(wmp_item)

		after_cream_transfer_diary, inter_stock_transfer_cream = interCreamTransfer(shortage_list_cream, surplus_list_cream,
																					diary_list)

		after_cream_balancing_diarylist,cream_purchased,cream_sold = creamBalancingReport(after_cream_transfer_diary)





		cream_purchased_union+=cream_purchased
		cream_sold_union+=cream_sold



		total_milk_handled_month=wm_procurement_union+wm_purchase_union+wm_reconstitution_union

		total_milk_handled[month]=total_milk_handled_month

		wm_requirement_product[month]=wm_requirement_product_month


		total_sm_required[month]=total_sm_union

		total_milk_required_products[month]=total_milk_required_union

		try:
			milk_diverted=(total_milk_required_union / total_milk_handled_month) * 100
		except Exception as e:
			milk_diverted=0
			print "Exception Handled reportAnnual in 2483"

		milk_diverted_percentage[month] =milk_diverted
		wm_surplus_sale[month]=wm_surplus_sale_union


		try:
			distress_milk = (wm_surplus_sale_union / total_milk_handled_month) * 100
		except Exception as e:
			distress_milk=0
			print "Exception Handled reportAnnual in 2487"


		distress_milk_percentage[month]=distress_milk

		csm_surplus_sale[month]=csm_surplus_sale_union

		csm_converted_smp[month]=csm_converted_smp_union
		total_cream_handled_union=(cream_reconstitution_union+total_month_requirement_cream)
		total_cream_handled[month]=total_cream_handled_union




		targetYear=(ConfigurationAttribute.objects.first().financial_Year+1)
		no_of_days=calendar.monthrange(targetYear, month)[1]
		try:

			total_cream_matric[month]=(total_cream_handled_union/1000)*no_of_days
		except Exception as e:
			total_cream_matric[month]=0
			print "Exception handled in reportAnnual 2506"

		total_cream_required[month]=total_cream_required_union

		total_cream_purchased[month]=cream_purchased_union
		total_cream_sold[month]=cream_sold_union
		try:
			distress_cream_percentage[month]=(cream_sold_union/total_cream_handled_union)*100

		except Exception as e:
			distress_cream_percentage[month]=0
			print "Exception handled in reportAnnual 2517" + str(e)
		try:
			wm_purchase_percentage[month]=(wm_purchase_union/total_milk_handled_month)*100
		except Exception as e:
			wm_purchase_percentage[month]=0
			print "Exception handled in reportAnnual 2522" + str(e)
		total_smp_purchased[month]=total_smp_purchased_union
		total_smp_sold[month]=total_smp_sold_union
		total_smp_recieved[month]=total_smp_recieved_union
		total_wmp_sold[month]=total_wmp_sold_union
		total_wmp_purchased[month]=total_wmp_purchased_union




	for category in CategoryList:

		category_sale = []
		for month in MONTHS.items():

			salesum = 0
			saledetails = ActualSale.objects.filter(product__in=(Product.objects.filter(category=category)).values('code'),
												month=month[0])

			for sale in saledetails:
				salesum += sale.targetSalesUnit

			category_sale_month={'month':month[0],'value':salesum}
			category_sale.append(category_sale_month)


		# print category_sale
		category_sale_list[category.name]=category_sale
		# category_sale_list.append(category_sale_item)


	return render(request, 'prediction/ReportAnnualTally.html',{'total_milk_handled':total_milk_handled,'month':month_list,
	'wm_requirement_product':wm_requirement_product,'total_sm_required':total_sm_required,'total_milk_required_products':total_milk_required_products
	,'milk_diverted_percentage':milk_diverted_percentage,'wm_surplus_sale':wm_surplus_sale,'distress_milk_percentage':distress_milk_percentage
	,'csm_surplus_sale':csm_surplus_sale,'csm_converted_smp':csm_converted_smp,'total_cream_handled':total_cream_handled,'total_cream_matric':total_cream_matric
	,'total_cream_required':total_cream_required,'total_cream_purchased':total_cream_purchased,'total_cream_sold':total_cream_sold
	,'distress_cream_percentage':distress_cream_percentage,'wm_purchase_percentage':wm_purchase_percentage,'total_smp_purchased':total_smp_purchased
	,'total_smp_sold':total_smp_sold,'total_smp_recieved':total_smp_recieved,'total_wmp_sold':total_wmp_sold,
	'total_wmp_purchased':total_wmp_purchased,'category_sale_list':category_sale_list})


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

				total_month_requirement_smp = month_requirement_for_milk_issue_production_smp + month_issue_requirement_sales_smp

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
						smp_item={'transaction':'SMP Sold:'+str(item_smp['total_smp_used'])+" ,Amount:"+str(item_smp['total_smp_used']*sale_rate),'diary':item_smp['diary'].name}

					except Exception as e:
						print "Exception handled At 2034"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='13').value
						smp_item = {'transaction': 'SMP Purchased:' + str(
								item_smp['total_smp_used']) + " ,Amount:" + str(
								item_smp['total_smp_used'] * rate),'diary':item_smp['diary'].name}


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
									item_wmp['total_wmp_used']) + " ,Amount:" + str(
									item_wmp['total_wmp_used'] * sale_rate),'diary':item_wmp['diary'].name}

					except Exception as e:
						print "Exception handled At 2078"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='11').value
						wmp_item = {'transaction': 'WMP Purchased:' + str(
								item_wmp['total_wmp_used']) + " ,Amount:" + str(
									item_wmp['total_wmp_used'] * rate),'diary':item_wmp['diary'].name}

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
			elif data['calculation_Name']=='4':
				if GeneralCalculation.objects.get(code='5').value!=0 and data['value']!=0:
					if (data['value']+GeneralCalculation.objects.get(code='5').value)==100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of Surplus WM(Sold+Converted) Must Be 100")
				else:
					calculation_obj.save()
			elif data['calculation_Name']=='5':
				if data['value']!=0 and GeneralCalculation.objects.get(code='4').value!=0:
					if (data['value'] + GeneralCalculation.objects.get(code='4').value) == 100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of Surplus WM(Sold+Converted) Must Be 100")
				else:
					calculation_obj.save()
			elif data['calculation_Name']=='6':
				if GeneralCalculation.objects.get(code='7').value!=0 and data['value']!=0:
					if (data['value']+GeneralCalculation.objects.get(code='7').value)==100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of CSM(Sold+Converted) Must Be 100")
				else:
					calculation_obj.save()
			elif data['calculation_Name']=='7':
				if data['value']!=0 and GeneralCalculation.objects.get(code='6').value!=0:
					if (data['value'] + GeneralCalculation.objects.get(code='6').value) == 100:
						calculation_obj.save()
					else:
						messages.info(request,"Percentage Of CSM(Sold+Converted) Must Be 100")
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

@login_required
@user_passes_test(group_check_diary)
def reportMAT(request):
	# region Fat and SNF
	wm_fat = 0
	wm_snf = 0
	cream_fat=0
	cream_snf=0
	smp_snf=0
	std_fat=0
	std_snf=0
	tm_fat=0
	tm_snf=0
	jersey_fat=0
	jersey_snf=0
	htm_fat = 0
	htm_snf = 0
	dtm_fat=0
	dtm_snf=0
	sm_fat=0
	sm_snf=0
	wmp_fat=0
	wmp_snf=0
	csm_fat=0
	csm_snf=0

	try:

		issue_obj = Issue.objects.get(name='WM')
		wm_fat = issue_obj.fat
		wm_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT Issue WM Fetching failed"

	try:
		issue_obj = Issue.objects.get(name='CREAM')
		cream_fat=issue_obj.fat
		cream_snf=issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT CREAM Fetching Failed"

	try:

		issue_obj = Issue.objects.get(name='SMP')
		smp_snf=issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT SMP fetching failed"
	try:
		issue_obj = Issue.objects.get(name='STD')
		std_fat = issue_obj.fat
		std_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT STD fetching failed"
	try:
		issue_obj = Issue.objects.get(name='TM')
		tm_fat = issue_obj.fat
		tm_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT TM fetching failed"

	try:
		issue_obj = Issue.objects.get(name='JERSY')
		jersey_fat = issue_obj.fat
		jersey_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT JERSEY fetching failed"

	try:
		issue_obj = Issue.objects.get(name='HTM')
		htm_fat = issue_obj.fat
		htm_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT HTM fetching failed"

	try:
		issue_obj = Issue.objects.get(name='DTM')
		dtm_fat = issue_obj.fat
		dtm_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT DTM fetching failed"

	try:
		issue_obj = Issue.objects.get(name='SM')
		sm_fat = issue_obj.fat
		sm_snf = issue_obj.snf
	except Exception as e:
		print "Exception Handled in reportMAT SM fetching failed"

	try:
		wmp_fat = GeneralCalculation.objects.get(code='18').value
		wmp_snf = GeneralCalculation.objects.get(code='19').value
	except Exception as e:
		print "Exception Handled in reportMAT WMP fetching failed"
	try:
		csm_fat=GeneralCalculation.objects.get(code='17').value
	except Exception as e:
		print "Exception Handled in reportMAT CSM fetching failed"






	# endregion
	#region Dictionary Initialization

	wm_procurement_list=[]
	current_diary = diary_of_user(request.user)
	wm_stock_out_transfer_list=OrderedDict()
	wm_stock_in_transfer_list =OrderedDict()
	wm_purchase_list=OrderedDict()
	wm_surplus_sale_list=OrderedDict()
	wm_reconstitution_list=OrderedDict()
	month_list = OrderedDict()
	wm_input_total=OrderedDict()
	wm_requirement_product = OrderedDict()
	wm_std_production=OrderedDict()
	wm_Jersey_production = OrderedDict()
	wm_tm_production = OrderedDict()
	wm_htm_production = OrderedDict()
	wm_dtm_production = OrderedDict()
	wm_sm_production = OrderedDict()
	wm_surplus_csm=OrderedDict()
	cream_surplus_csm=OrderedDict()
	wm_output_total = OrderedDict()
	cream_std_production=OrderedDict()
	cream_Jersey_production = OrderedDict()
	cream_tm_production = OrderedDict()
	cream_htm_production = OrderedDict()
	cream_dtm_production = OrderedDict()
	cream_sm_production = OrderedDict()

	smp_std_production = OrderedDict()
	smp_Jersey_production = OrderedDict()
	smp_tm_production = OrderedDict()
	smp_htm_production = OrderedDict()
	smp_dtm_production = OrderedDict()
	smp_sm_production = OrderedDict()

	std_input_total = OrderedDict()
	Jersey_input_total = OrderedDict()
	tm_input_total = OrderedDict()
	htm_input_total = OrderedDict()
	dtm_input_total = OrderedDict()
	sm_input_total = OrderedDict()
	rc_input_total=OrderedDict()

	std_output_total = OrderedDict()
	Jersey_output_total = OrderedDict()
	tm_output_total = OrderedDict()
	htm_output_total = OrderedDict()
	dtm_output_total = OrderedDict()
	sm_output_total = OrderedDict()
	rc_output_total=OrderedDict()

	total_std_requirement=OrderedDict()
	total_Jersey_requirement = OrderedDict()
	total_tm_requirement = OrderedDict()
	total_htm_requirement = OrderedDict()
	total_dtm_requirement = OrderedDict()
	total_sm_requirement = OrderedDict()

	cream_rc_requirement=OrderedDict()
	smp_rc_smp_requirement=OrderedDict()
	smp_rc_wmp_requirement=OrderedDict()
	water_rc_smp_requirement=OrderedDict()
	water_rc_wmp_requirement=OrderedDict()
	wmp_rc_wmp_requirement=OrderedDict()
	cream_purchase_list=OrderedDict()
	cream_stock_in_transfer_list=OrderedDict()
	cream_stock_out_transfer_list=OrderedDict()
	cream_input_total=OrderedDict()
	cream_output_total = OrderedDict()

	cream_requirement_product=OrderedDict()
	cream_sale_list=OrderedDict()


	smp_purchase_list=OrderedDict()
	smp_from_conversion=OrderedDict()

	smp_input_total=OrderedDict()

	smp_requirement=OrderedDict()

	smp_sale_list=OrderedDict()

	smp_output_total=OrderedDict()
	csm_produced=OrderedDict()
	csm_input_total=OrderedDict()


	csm_sale_list=OrderedDict()

	csm_for_conversion=OrderedDict()

	csm_output_total=OrderedDict()


	#endregion

	#region YearWise Total Initialization
	wm_procurement_year=0
	wm_purchase_year=0
	wm_reconstitution_year=0
	wm_requirement_product_year=0
	wm_std_production_year=0
	wm_Jersey_production_year=0
	wm_htm_production_year=0
	wm_dtm_production_year=0
	wm_sm_production_year=0
	wm_surplus_sale_year=0
	wm_surplus_csm_year=0
	cream_std_production_year=0
	smp_std_production_year=0
	total_std_requirement_year=0
	wm_tm_production_year=0
	cream_tm_production_year=0
	smp_tm_production_year=0
	total_tm_requirement_year=0
	cream_Jersey_production_year=0
	smp_Jersey_production_year=0
	total_Jersey_requirement_year=0
	cream_htm_production_year=0
	smp_htm_production_year=0
	total_htm_requirement_year=0
	cream_dtm_production_year=0
	smp_dtm_production_year=0
	total_dtm_requirement_year=0
	cream_sm_production_year=0
	smp_sm_production_year=0
	total_sm_requirement_year=0
	cream_rc_requirement_year=0
	smp_rc_smp_requirement_year=0
	smp_rc_wmp_requirement_year=0
	water_rc_smp_requirement_year=0
	water_rc_wmp_requirement_year=0
	wmp_rc_wmp_requirement_year=0
	cream_purchase_year=0
	cream_surplus_csm_year=0
	cream_requirement_product_year=0
	cream_sale_list_year=0
	smp_purchase_list_year=0
	smp_from_conversion_year=0
	smp_requirement_year=0
	smp_sale_list_year=0
	csm_produced_year=0
	csm_sale_list_year=0
	csm_for_conversion_year=0
	#endregion

	#region MonthWise Operations
	for month_item in MONTHS.items():

		# region Initialization
		wm_purchase_month=0
		wm_reconstitution_month=0


		issue_wm = Issue.objects.get(name='WM')

		issue_cream = Issue.objects.get(name='CREAM')
		issue_smp = Issue.objects.get(name='SMP')

		month = month_item[0]
		month_list[month] = month_item[1]

		resultitem = []

		cream_requirement_list = []

		smp_requirement_list = []

		wmp_requirement_list = []
		shortage_list = OrderedDict()
		surplus_list = OrderedDict()

		fwm = issue_wm.fat

		diary_list = Diary.objects.all()
		total_requirement_diary_cpd = 0
		wm_procurement_month=0
		wm_requirement_product_month=0
		wm_std_production_month=0
		wm_Jersey_production_month=0
		wm_tm_production_month=0
		wm_dtm_production_month=0
		wm_htm_production_month=0
		wm_sm_production_month=0

		cream_std_production_month=0
		cream_Jersey_production_month=0
		cream_tm_production_month=0
		cream_dtm_production_month=0
		cream_htm_production_month=0
		cream_sm_production_month=0

		smp_std_production_month=0
		smp_Jersey_production_month=0
		smp_tm_production_month=0
		smp_dtm_production_month=0
		smp_htm_production_month=0
		smp_sm_production_month=0

		cream_requirement_product_month=0

		smp_purchase_month=0
		smp_requirement_month=0
		smp_sale_month=0



		# endregion
		for diary in diary_list:

			ret_month, month_issue_requirement_sales_wm = totalIssueRequirement(month, diary, issue_wm)
			ret_month, month_issue_requirement_sales_cream = totalIssueRequirement(month, diary, issue_cream)

			ret_month, month_issue_requirement_sales_smp = totalIssueRequirement(month, diary, issue_smp)


			if diary.name==current_diary.name:
				m, issueasproduct_wm = IssueasProduct(month, diary, issue_wm)

				wm_requirement_product_month += month_issue_requirement_sales_wm-issueasproduct_wm

				m, issueasproduct_cream = IssueasProduct(month, diary, issue_cream)

				cream_requirement_product_month+=month_issue_requirement_sales_cream-issueasproduct_cream






			month_requirement_for_milk_issue_production_wm = 0
			month_requirement_for_milk_issue_production_cream = 0
			month_requirement_for_milk_issue_production_smp = 0
			type2_issue_list = Issue.objects.filter(type='2')

			for issue_item in type2_issue_list:

				month_issue_requirement=0

				try:

					issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)


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
					print "Exception handled reportMAT in line no 3036"

				requirement_to_produce_milk_issue_wm = month_issue_requirement * composition_ratio_derived_wm
				month_requirement_for_milk_issue_production_wm += requirement_to_produce_milk_issue_wm




				requirement_to_produce_milk_issue_cream = month_issue_requirement * composition_ratio_derived_cream
				month_requirement_for_milk_issue_production_cream += requirement_to_produce_milk_issue_cream

				requirement_to_produce_milk_issue_smp = month_issue_requirement * composition_ratio_derived_smp
				month_requirement_for_milk_issue_production_smp += requirement_to_produce_milk_issue_smp

				if diary.name==current_diary.name:


					if issue_item.name.upper()=="STD":
						wm_std_production[month]=requirement_to_produce_milk_issue_wm
						wm_std_production_month=requirement_to_produce_milk_issue_wm
						wm_std_production_year+=wm_std_production_month


						cream_std_production[month]=requirement_to_produce_milk_issue_cream
						cream_std_production_month=requirement_to_produce_milk_issue_cream
						cream_std_production_year+=cream_std_production_month
						smp_std_production[month]=requirement_to_produce_milk_issue_smp
						smp_std_production_month=requirement_to_produce_milk_issue_smp
						smp_std_production_year+=smp_std_production_month

						total_std_requirement[month]=month_issue_requirement
						total_std_requirement_year+=month_issue_requirement

					elif issue_item.name.upper()=="JERSY":
						wm_Jersey_production[month]= requirement_to_produce_milk_issue_wm
						wm_Jersey_production_month=requirement_to_produce_milk_issue_wm
						wm_Jersey_production_year+=wm_Jersey_production_month
						cream_Jersey_production[month]=requirement_to_produce_milk_issue_cream
						cream_Jersey_production_month=requirement_to_produce_milk_issue_cream
						cream_Jersey_production_year+=cream_Jersey_production_month

						smp_Jersey_production[month]=requirement_to_produce_milk_issue_smp
						smp_Jersey_production_month=requirement_to_produce_milk_issue_smp
						smp_Jersey_production_year+=smp_Jersey_production_month


						total_Jersey_requirement[month]=month_issue_requirement
						total_Jersey_requirement_year+=month_issue_requirement

					elif issue_item.name.upper()=="TM":
						wm_tm_production[month] = requirement_to_produce_milk_issue_wm
						wm_tm_production_month=requirement_to_produce_milk_issue_wm
						wm_tm_production_year+=wm_tm_production_month

						cream_tm_production[month]=requirement_to_produce_milk_issue_cream
						cream_tm_production_month=requirement_to_produce_milk_issue_cream
						cream_tm_production_year+=cream_tm_production_month

						smp_tm_production[month]=requirement_to_produce_milk_issue_smp
						smp_tm_production_month=requirement_to_produce_milk_issue_smp
						smp_tm_production_year+=smp_tm_production_month

						total_tm_requirement[month]=month_issue_requirement
						total_tm_requirement_year+=month_issue_requirement
					elif issue_item.name.upper()=="DTM":

						wm_dtm_production[month] = requirement_to_produce_milk_issue_wm
						wm_dtm_production_month=requirement_to_produce_milk_issue_wm
						wm_dtm_production_year+=wm_dtm_production_month


						cream_dtm_production[month]=requirement_to_produce_milk_issue_cream
						cream_dtm_production_month=requirement_to_produce_milk_issue_cream
						cream_dtm_production_year+=cream_dtm_production_month

						smp_dtm_production[month]=requirement_to_produce_milk_issue_smp
						smp_dtm_production_month=requirement_to_produce_milk_issue_smp
						smp_dtm_production_year+=smp_dtm_production_month

						total_dtm_requirement[month]=month_issue_requirement
						total_dtm_requirement_year+=month_issue_requirement

					elif issue_item.name.upper()=="HTM":
						wm_htm_production[month] = requirement_to_produce_milk_issue_wm
						wm_htm_production_month=requirement_to_produce_milk_issue_wm
						wm_htm_production_year+=wm_htm_production_month

						cream_htm_production[month]=requirement_to_produce_milk_issue_cream
						cream_htm_production_month=requirement_to_produce_milk_issue_cream
						cream_htm_production_year+=cream_htm_production_month


						smp_htm_production[month]=requirement_to_produce_milk_issue_smp
						smp_htm_production_month=requirement_to_produce_milk_issue_smp
						smp_htm_production_year+=smp_htm_production_month


						total_htm_requirement[month]=month_issue_requirement
						total_htm_requirement_year+=month_issue_requirement

					elif issue_item.name.upper()=="SM":
						wm_sm_production[month]= requirement_to_produce_milk_issue_wm
						wm_sm_production_month=requirement_to_produce_milk_issue_wm
						wm_sm_production_year+=wm_sm_production_month


						cream_sm_production[month]=requirement_to_produce_milk_issue_cream
						cream_sm_production_month=requirement_to_produce_milk_issue_cream
						cream_sm_production_year+=cream_sm_production_month

						smp_sm_production[month]=requirement_to_produce_milk_issue_smp
						smp_sm_production_month=requirement_to_produce_milk_issue_smp
						smp_sm_production_year+=smp_sm_production_month

						total_sm_requirement[month]=month_issue_requirement
						total_sm_requirement_year+=month_issue_requirement

			total_month_requirement_wm = month_requirement_for_milk_issue_production_wm + month_issue_requirement_sales_wm

			total_month_requirement_cream = month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_cream

			total_month_requirement_smp = month_requirement_for_milk_issue_production_smp + month_issue_requirement_sales_smp

			if diary.name==current_diary.name:
				smp_requirement_month+=total_month_requirement_smp

			wm_procurement_item =""
			total_month_procurement = 0
			try:
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)
				total_month_procurement = Awm_obj.targetProcurement
				if current_diary.name==diary.name:
					wm_procurement_item={'month':month,'value':total_month_procurement}
					wm_procurement_list.append(wm_procurement_item)
					wm_procurement_month += total_month_procurement
					wm_procurement_year+=total_month_procurement

			except Exception as e:
				print "Exception handled in line 3063"
				if current_diary.name==diary.name:
					if wm_procurement_item =="":
						wm_procurement_item = {'month': month, 'value': 0}
						wm_procurement_list.append(wm_procurement_item)



			difference = total_month_procurement - total_month_requirement_wm

			if difference != 0:
				type_of_difference = ""
				if difference >= 0:
					type_of_difference = "Surplus"
					surplus_list[diary.name] = difference
				else:
					type_of_difference = "Shortage"
					difference = difference * -1
					shortage_list[diary.name] = difference

				result = {"month": MONTHS[month], "diary": diary.name, "requirement": total_month_requirement_wm,
						  "procurement": total_month_procurement, "difference": difference, "type": type_of_difference}
				resultitem.append(result)

			if "CPD" == diary.id:
				total_requirement_diary_cpd = total_month_requirement_wm

			cream_requirement_item = {"month": MONTHS[month], "diary": diary,
									  "total_cream_used": 0 - total_month_requirement_cream, "type": "Surplus"}
			cream_requirement_list.append(cream_requirement_item)
			smp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_smp_used": 0 - total_month_requirement_smp, "type": "Sale"}
			smp_requirement_list.append(smp_requirement_item)

			wmp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_wmp_used": 0, "type": "Sale"}
			wmp_requirement_list.append(wmp_requirement_item)

		after_transfer_diary, inter_stock_transfer = interMilkTransfer(shortage_list, surplus_list,
																	   total_requirement_diary_cpd, diary_list)
		after_transfer_current_diary=[]
		for item in after_transfer_diary:
			if item['diary']==current_diary.name:
				after_transfer_current_diary.append(item)


		after_wm_balancing_diarylist, wm_reconstitution, wm_purchase, wm_sale, csm_sale, csm_converted, cream_reconstitution, converted_smp,wm_for_csm,smp_rc_smp,smp_rc_wmp,water_rc_smp,water_rc_wmp,wmp_rc_wmp,cream_for_csm,csm_produced_month,csm_for_conversion_month= wmBalancingReportDiaryWise(
			after_transfer_current_diary, month,current_diary.name)

		wm_purchase_month += wm_purchase
		wm_reconstitution_month+=wm_reconstitution
		wm_after_transfer = []

		shortage_list_cream = OrderedDict()
		surplus_list_cream = OrderedDict()

		cream_list = []
		for item_cream in cream_requirement_list:

			for item in after_wm_balancing_diarylist:
				if item['diary'] == current_diary.name:
					wm_after_transfer.append(item)

				if item_cream['diary'].name == item['diary']:
					requirement = item_cream['total_cream_used'] * (-1)
					item_cream['total_cream_used'] = 0 - (requirement + item['cream_used_csm'] + item['cream_used_smp'])

				if item_cream['total_cream_used'] < 0:
					item_cream['type'] = "Shortage"

					cream_used = item_cream['total_cream_used'] * (-1)
					shortage_list_cream[item_cream['diary']] = cream_used * (-1)


				elif item_cream['total_cream_used'] > 0:
					item_cream['type'] = "Surplus"
					surplus_list_cream[item_cream['diary']] = item_cream['total_cream_used']
			if item_cream['total_cream_used'] != 0:
				if item_cream['total_cream_used'] < 0:
					item_cream['total_cream_used'] = item_cream['total_cream_used'] * (-1)
				cream_list.append(item_cream)
		smp_after_transfer = []
		for item_smp in smp_requirement_list:

			for item in after_wm_balancing_diarylist:
				if item_smp['diary'].name == item['diary']:
					requirement = item_smp['total_smp_used'] * (-1)
					item_smp['total_smp_used'] = 0 - (
					requirement + item['smp_used_smp'] + item['smp_used_wmp'] - item['converted_smp'])

				if item_smp['total_smp_used'] < 0:
					item_smp['type'] = "Purchase"

					used = item_smp['total_smp_used'] * (-1)

					item_smp['total_smp_used'] = used

				elif item_smp['total_smp_used'] > 0:
					item_smp['type'] = "Sale"
			if item_smp['diary'].name == current_diary.name:

				if item_smp['type'] == "Sale":
					try:
						sale_rate = GeneralCalculation.objects.get(code='14').value
						smp_item = {'transaction': 'SMP Sold:' + str(
							item_smp['total_smp_used']) + " ,Amount:" + str(
							item_smp['total_smp_used'] * sale_rate)}
						smp_sale_month+=item_smp['total_smp_used']

					except Exception as e:
						print "Exception handled At 3160"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='13').value
						smp_item = {'transaction': 'SMP Purchased:' + str(
							item_smp['total_smp_used']) + " ,Amount:" + str(
							item_smp['total_smp_used'] * rate)}
						smp_purchase_month+=item_smp['total_smp_used']

					except Exception as e:
						print "Exception handled At 3169"

				smp_after_transfer.append(smp_item)
		wmp_after_transfer = []
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
			if item_wmp['diary'].name == current_diary.name:

				if item_wmp['type'] == "Sale":
					try:
						sale_rate = GeneralCalculation.objects.get(code='12').value
						wmp_item = {'transaction': 'WMP Sold:' + str(
							item_wmp['total_wmp_used']) + " ,Amount:" + str(
							item_wmp['total_wmp_used'] * sale_rate)}

					except Exception as e:
						print "Exception handled At 3198"
				else:
					try:
						rate = GeneralCalculation.objects.get(code='11').value
						wmp_item = {'transaction': 'WMP Purchased:' + str(
							item_wmp['total_wmp_used']) + " ,Amount:" + str(
							item_wmp['total_wmp_used'] * rate)}

					except Exception as e:
						print "Exception handled At 3207"

				wmp_after_transfer.append(wmp_item)

		after_cream_transfer_diary, inter_stock_transfer_cream = interCreamTransfer(shortage_list_cream,
																					surplus_list_cream,
																					diary_list)

		after_cream_balancing_diarylist,cream_purchase,cream_sale = creamBalancingReportDiaryWise(after_cream_transfer_diary,current_diary.name)

		wm_requirement_product[month] = wm_requirement_product_month
		wm_requirement_product_year+=wm_requirement_product_month
		cream_requirement_product[month]=cream_requirement_product_month
		cream_requirement_product_year+=cream_requirement_product_month


		cream_rc_requirement[month]=cream_reconstitution
		cream_rc_requirement_year+=cream_reconstitution

		smp_rc_smp_requirement[month]=smp_rc_smp
		smp_rc_smp_requirement_year+=smp_rc_smp
		smp_rc_wmp_requirement[month]=smp_rc_wmp
		smp_rc_wmp_requirement_year+=smp_rc_wmp
		water_rc_smp_requirement[month]=water_rc_smp
		water_rc_smp_requirement_year+=water_rc_smp
		water_rc_wmp_requirement[month]=water_rc_wmp
		water_rc_wmp_requirement_year+=water_rc_wmp
		wmp_rc_wmp_requirement[month]=wmp_rc_wmp
		wmp_rc_wmp_requirement_year+=wmp_rc_wmp

		cream_purchase_list[month]=cream_purchase
		cream_purchase_year+=cream_purchase
		cream_sale_list[month]=cream_sale
		cream_sale_list_year+=cream_sale

		smp_from_conversion[month]=csm_converted
		smp_from_conversion_year+=csm_converted

		smp_requirement[month]=smp_requirement_month
		smp_requirement_year+=smp_requirement_month
		smp_purchase_list[month]=smp_purchase_month
		smp_purchase_list_year+=smp_purchase_month
		smp_sale_list[month]=smp_sale_month
		smp_sale_list_year+=smp_sale_month


		cream_after_transfer = []

		for item in after_cream_balancing_diarylist:
			if item['diary'].name == current_diary.name:
				cream_after_transfer.append(item)

		if not bool(wm_after_transfer):
			transaction_item = {'after_transfer': 'Balanced'}
			wm_after_transfer.append(transaction_item)

		wm_stockin_month=0
		wm_stockout_month=0

		for item in inter_stock_transfer:
			if item['diary']==current_diary.name:


				if item['type']=='to':




					stockout_item={'month':month,'value':item['value']}
					wm_stock_out_transfer_list[item['to_or_from_diary']]=stockout_item
					wm_stockout_month+=item['value']
				else:
					stockin_item = {'month': month , 'value': item['value']}
					wm_stock_in_transfer_list[item['to_or_from_diary']]=stockin_item
					wm_stockin_month +=item['value']
		cream_stockin_month=0
		cream_stockout_month=0
		for item in inter_stock_transfer_cream:
			if item['diary']==current_diary.name:
				if item['type']=='to':

					stockout_item={'month':month,'value':item['value']}
					cream_stock_out_transfer_list[item['to_or_from_diary']]=stockout_item
					cream_stockout_month+=item['value']
				else:
					stockin_item = {'month': month , 'value': item['value']}
					cream_stock_in_transfer_list[item['to_or_from_diary']]=stockin_item
					cream_stockin_month +=item['value']









		wm_purchase_list[month]=wm_purchase_month
		wm_purchase_year+=wm_purchase_month
		wm_reconstitution_list[month]=wm_reconstitution_month
		wm_reconstitution_year+=wm_reconstitution_month
		wm_surplus_sale_list[month]=wm_sale
		wm_surplus_sale_year+=wm_sale

		wm_input_total[month]=wm_purchase_month+wm_reconstitution_month+wm_stockin_month+wm_procurement_month
		wm_output_total[month]=wm_requirement_product_month+wm_std_production_month+wm_Jersey_production_month+wm_tm_production_month+wm_htm_production_month+wm_dtm_production_month+wm_sm_production_month+wm_stockout_month+wm_sale+wm_for_csm


		std_input_total[month]=wm_std_production_month+cream_std_production_month+smp_std_production_month
		std_output_total[month]=total_std_requirement[month]


		tm_input_total[month]=wm_tm_production_month+cream_tm_production_month+smp_tm_production_month
		tm_output_total[month]=total_tm_requirement[month]

		Jersey_input_total[month]=wm_Jersey_production_month+cream_Jersey_production_month+smp_Jersey_production_month
		Jersey_output_total[month]=total_Jersey_requirement[month]

		htm_input_total[month]=wm_htm_production_month+cream_htm_production_month+smp_htm_production_month
		htm_output_total[month]=total_htm_requirement[month]

		dtm_input_total[month]=wm_dtm_production_month+cream_dtm_production_month+smp_dtm_production_month
		dtm_output_total[month]=total_dtm_requirement[month]

		sm_input_total[month]=wm_sm_production_month+cream_sm_production_month+smp_sm_production_month
		sm_output_total[month]=total_sm_requirement[month]

		rc_input_total[month]=cream_reconstitution+smp_rc_smp+smp_rc_wmp+water_rc_smp+water_rc_wmp+wmp_rc_wmp
		rc_output_total[month]=wm_reconstitution_list[month]

		wm_surplus_csm[month]=wm_for_csm
		wm_surplus_csm_year+=wm_for_csm
		cream_surplus_csm[month]=cream_for_csm
		cream_surplus_csm_year+=cream_for_csm

		cream_input_total[month]=cream_purchase+cream_stockin_month+cream_Jersey_production_month+cream_tm_production_month+cream_htm_production_month+cream_dtm_production_month+cream_sm_production_month+cream_for_csm
		cream_output_total[month]=cream_std_production_month+cream_reconstitution+cream_requirement_product_month+cream_stockout_month+cream_sale

		smp_input_total[month]=smp_purchase_month+csm_converted
		smp_output_total[month]=smp_requirement_month+smp_sale_month

		csm_produced[month]=csm_produced_month
		csm_produced_year+=csm_produced_month
		csm_input_total[month]=csm_produced_month

		csm_sale_list[month]=csm_sale
		csm_sale_list_year+=csm_sale
		csm_for_conversion[month]=csm_for_conversion_month
		csm_for_conversion_year+=csm_for_conversion_month

		csm_output_total[month]=cream_for_csm+csm_sale+csm_for_conversion_month
	#endregion

	#region Stockin and Stockout reordering of cream and wm
	wm_stock_in=[]
	wm_stockin_year=0
	wm_stockin_fat_year=0
	wm_stockin_snf_year = 0
	for diary, item_list in wm_stock_in_transfer_list.items():
		transfer=[]
		wm_stockin_diary_year=0
		for month in MONTHS.items():
			if item_list['month']!=month[0]:
				stock_item = {'month': month[0], 'value':0}
			else:
				stock_item = {'month': month[0], 'value': item_list['value']}
				wm_stockin_diary_year+=item_list['value']
			transfer.append(stock_item)
		stock_item = {'month': 13, 'value': wm_stockin_diary_year}
		transfer.append(stock_item)
		stock_item = {'month': 14, 'value': wm_fat}
		transfer.append(stock_item)
		stock_item = {'month': 15, 'value': ((wm_stockin_diary_year * wm_fat) / 100)}
		transfer.append(stock_item)
		stock_item = {'month': 16, 'value': wm_snf}
		transfer.append(stock_item)
		stock_item = {'month': 17, 'value': ((wm_stockin_diary_year * wm_snf) / 100)}
		transfer.append(stock_item)
		wm_stockin_fat_year += ((wm_stockin_diary_year * wm_fat) / 100)
		wm_stockin_snf_year+=((wm_stockin_diary_year * wm_snf)/ 100)




		wm_stockin_year+=wm_stockin_diary_year


		wm_stock_in_item={"diary":diary,"transfer":transfer}
		wm_stock_in.append(wm_stock_in_item)
	wm_stock_out = []
	wm_stock_out_year = 0
	wm_stock_out_fat_year=0
	wm_stock_out_snf_year = 0
	for diary, item_list in wm_stock_out_transfer_list.items():
		transfer=[]
		wm_stock_out_year_diary=0
		for month in MONTHS.items():
			if item_list['month']!=month[0]:
				stock_item = {'month': month[0], 'value':0}
			else:
				stock_item = {'month': month[0], 'value': item_list['value']}
				wm_stock_out_year_diary+=item_list['value']
			transfer.append(stock_item)
		stock_item = {'month': 13, 'value': wm_stock_out_year_diary}
		wm_stock_out_year+=wm_stock_out_year_diary
		transfer.append(stock_item)

		stock_item = {'month': 14, 'value': wm_fat}
		transfer.append(stock_item)
		stock_item = {'month': 15, 'value': ((wm_stock_out_year_diary * wm_fat) / 100)}
		wm_stock_out_fat_year += ((wm_stock_out_year_diary * wm_fat) / 100)
		wm_stock_out_snf_year+=((wm_stock_out_year_diary * wm_snf)/ 100)
		transfer.append(stock_item)
		stock_item = {'month': 16, 'value': wm_snf}
		transfer.append(stock_item)
		stock_item = {'month': 17, 'value': ((wm_stock_out_year_diary * wm_snf) / 100)}
		transfer.append(stock_item)



		wm_stock_out_item={"diary":diary,"transfer":transfer}
		wm_stock_out.append(wm_stock_out_item)

	cream_stock_in = []
	cream_stockin_year=0
	cream_stock_in_fat_year=0
	cream_stock_in_snf_year = 0
	for diary, item_list in cream_stock_in_transfer_list.items():
		transfer = []
		cream_stockin_diary=0
		for month in MONTHS.items():
			if item_list['month'] != month[0]:
				stock_item = {'month': month[0], 'value': 0}
			else:
				stock_item = {'month': month[0], 'value': item_list['value']}
				cream_stockin_diary+=item_list['value']
			transfer.append(stock_item)
		stock_item = {'month': 13, 'value': cream_stockin_diary}
		transfer.append(stock_item)
		cream_stockin_year+=cream_stockin_diary


		stock_item = {'month': 14, 'value': cream_fat}
		transfer.append(stock_item)
		stock_item = {'month': 15, 'value': ((cream_stockin_diary * cream_fat) / 100)}
		cream_stock_in_fat_year += ((cream_stockin_diary * cream_fat) / 100)
		cream_stock_in_snf_year += ((cream_stockin_diary * cream_snf) / 100)
		transfer.append(stock_item)
		stock_item = {'month': 16, 'value': cream_snf}
		transfer.append(stock_item)
		stock_item = {'month': 17, 'value': ((cream_stockin_diary * cream_snf) / 100)}
		transfer.append(stock_item)
		cream_stock_in_item = {"diary": diary, "transfer": transfer}
		cream_stock_in.append(cream_stock_in_item)

	cream_stockout_year = 0
	cream_stock_out = []
	cream_stock_out_fat_year=0
	cream_stock_out_snf_year=0

	for diary, item_list in cream_stock_out_transfer_list.items():
		transfer = []
		cream_stockout_diary = 0
		for month in MONTHS.items():
			if item_list['month'] != month[0]:
				stock_item = {'month': month[0], 'value': 0}
			else:
				stock_item = {'month': month[0], 'value': item_list['value']}
				cream_stockout_diary+=item_list['value']
			transfer.append(stock_item)
		stock_item = {'month': 13, 'value': cream_stockout_diary}
		transfer.append(stock_item)
		cream_stockout_year+=cream_stockout_diary
		stock_item = {'month': 14, 'value': cream_fat}
		transfer.append(stock_item)
		stock_item = {'month': 15, 'value': ((cream_stockout_diary * cream_fat) / 100)}
		cream_stock_out_fat_year += ((cream_stockout_diary * cream_fat) / 100)
		cream_stock_out_snf_year += ((cream_stockout_diary * cream_snf) / 100)
		transfer.append(stock_item)
		stock_item = {'month': 16, 'value': cream_snf}
		transfer.append(stock_item)
		stock_item = {'month': 17, 'value': ((cream_stockout_diary * cream_snf) / 100)}
		transfer.append(stock_item)
		cream_stock_out_item = {"diary": diary, "transfer": transfer}
		cream_stock_out.append(cream_stock_out_item)
	#endregion



	#region Additional Columns
	#region WM Tally Table

	wm_procurement_item = {'month': 13, 'value': wm_procurement_year}
	wm_procurement_list.append(wm_procurement_item)
	wm_procurement_item = {'month': 14, 'value': wm_fat}
	wm_procurement_list.append(wm_procurement_item)
	wm_procurement_item = {'month': 15, 'value': ((wm_procurement_year*wm_fat)/100)}
	wm_procurement_list.append(wm_procurement_item)
	wm_procurement_item = {'month': 16, 'value': wm_snf}
	wm_procurement_list.append(wm_procurement_item)
	wm_procurement_fat_year=((wm_procurement_year*wm_fat)/100)
	wm_procurement_snf_year=((wm_procurement_year*wm_snf)/100)
	wm_procurement_item = {'month': 17, 'value': ((wm_procurement_year*wm_snf)/100)}
	wm_procurement_list.append(wm_procurement_item)

	wm_purchase_list[13]=wm_purchase_year
	wm_purchase_list[14] = wm_fat
	wm_purchase_list[15] = (wm_purchase_year*wm_fat)/100
	wm_purchase_list[16] = wm_snf
	wm_purchase_list[17] = (wm_purchase_year*wm_snf)/100

	wm_reconstitution_list[13]=wm_reconstitution_year
	wm_reconstitution_list[14] = wm_fat
	wm_reconstitution_list[15]=(wm_reconstitution_year*wm_fat)/100
	wm_reconstitution_list[16]=wm_snf
	wm_reconstitution_list[17]=(wm_reconstitution_year*wm_snf)/100


	wm_input_total[13]=wm_procurement_year+wm_purchase_year+wm_reconstitution_year+wm_stockin_year
	wm_input_total[14]=wm_fat
	wm_input_total[15]=wm_procurement_fat_year+wm_purchase_list[15]+wm_reconstitution_list[15]+wm_stockin_fat_year
	wm_input_total[16] = wm_snf
	wm_input_total[17] = wm_procurement_snf_year + wm_purchase_list[17] + wm_reconstitution_list[17] + wm_stockin_snf_year



	wm_requirement_product[13]=wm_requirement_product_year
	wm_requirement_product[14] = wm_fat
	wm_requirement_product[15] = (wm_requirement_product_year*wm_fat)/100
	wm_requirement_product[16] = wm_snf
	wm_requirement_product[17] = (wm_requirement_product_year*wm_snf)/100



	wm_std_production[13]=wm_std_production_year
	wm_std_production[14] = wm_fat
	wm_std_production[15] = (wm_std_production_year*wm_fat)/100
	wm_std_production[16] = wm_snf
	wm_std_production[17] = (wm_std_production_year*wm_snf)/100


	wm_Jersey_production[13]=wm_Jersey_production_year
	wm_Jersey_production[14] = wm_fat
	wm_Jersey_production[15] = (wm_Jersey_production_year*wm_fat)/100
	wm_Jersey_production[16] = wm_snf
	wm_Jersey_production[17] = (wm_Jersey_production_year*wm_snf)/100


	wm_htm_production[13]=wm_htm_production_year
	wm_htm_production[14] = wm_fat
	wm_htm_production[15] = (wm_htm_production_year*wm_fat)/100
	wm_htm_production[16] = wm_snf
	wm_htm_production[17] = (wm_htm_production_year * wm_snf) / 100



	wm_dtm_production[13]=wm_dtm_production_year
	wm_dtm_production[14] = wm_fat
	wm_dtm_production[15] = (wm_dtm_production_year*wm_fat)/100
	wm_dtm_production[16] = wm_snf
	wm_dtm_production[17] = (wm_dtm_production_year*wm_snf)/100




	wm_sm_production[13]=wm_sm_production_year
	wm_sm_production[14] = wm_fat
	wm_sm_production[15] = (wm_sm_production_year*wm_fat)/100
	wm_sm_production[16] = wm_snf
	wm_sm_production[17] = (wm_sm_production_year*wm_snf)/100



	wm_surplus_sale_list[13]=wm_surplus_sale_year
	wm_surplus_sale_list[14] = wm_fat
	wm_surplus_sale_list[15] = (wm_surplus_sale_year*wm_fat)/100
	wm_surplus_sale_list[16] = wm_snf
	wm_surplus_sale_list[17] = (wm_surplus_sale_year*wm_snf)/100




	wm_surplus_csm[13]=wm_surplus_csm_year
	wm_surplus_csm[14] = wm_fat
	wm_surplus_csm[15] = (wm_surplus_csm_year*wm_fat)/100
	wm_surplus_csm[16] = wm_snf
	wm_surplus_csm[17] = (wm_surplus_csm_year*wm_snf)/100



	wm_tm_production[13] = wm_tm_production_year
	wm_tm_production[14] = wm_fat
	wm_tm_production[15] = (wm_tm_production_year*wm_fat)/100
	wm_tm_production[16] = wm_snf
	wm_tm_production[17] = (wm_tm_production_year * wm_snf) / 100





	wm_output_total[13]=wm_requirement_product_year+wm_std_production_year+wm_Jersey_production_year+wm_htm_production_year+wm_dtm_production_year+wm_sm_production_year+wm_stock_out_year+wm_surplus_sale_year+wm_surplus_csm_year+wm_tm_production_year
	wm_output_total[14]=wm_fat
	wm_output_total[15]=wm_tm_production[15]+wm_stock_out_fat_year+wm_surplus_csm[15]+wm_surplus_sale_list[15]+wm_sm_production[15]+wm_dtm_production[15]+wm_htm_production[15]+wm_Jersey_production[15]+wm_std_production[15]+wm_requirement_product[15]
	wm_output_total[16] = wm_snf
	wm_output_total[17] =wm_tm_production[17]+wm_stock_out_snf_year+wm_surplus_csm[17]+wm_surplus_sale_list[17]+wm_sm_production[17]+wm_dtm_production[17]+wm_htm_production[17]+wm_Jersey_production[17]+wm_std_production[17]+wm_requirement_product[17]

	#endregion

	#region STD
	cream_std_production[13]=cream_std_production_year
	cream_std_production[14] = cream_fat
	cream_std_production[15]=(cream_std_production_year*cream_fat)/100
	cream_std_production[16] = cream_snf
	cream_std_production[17] = (cream_std_production_year*cream_snf)/100



	smp_std_production[13]=smp_std_production_year
	smp_std_production[14]=0
	smp_std_production[15] = 0
	smp_std_production[16] = smp_snf
	smp_std_production[17] = (smp_snf*smp_std_production_year)/100



	std_input_total[13]=wm_std_production_year+cream_std_production_year+smp_std_production_year
	std_input_total[14]=0
	std_input_total[15]=wm_std_production[15]+cream_std_production[15]
	std_input_total[16]=0
	std_input_total[17]=wm_std_production[17]+cream_std_production[17]+smp_std_production[17]

	total_std_requirement[13]=total_std_requirement_year
	total_std_requirement[14]=std_fat
	total_std_requirement[15]=(total_std_requirement_year*std_fat)/100
	total_std_requirement[16]=std_snf
	total_std_requirement[17] = (total_std_requirement_year*std_snf)/100




	std_output_total[13]=total_std_requirement_year
	std_output_total[14]=std_fat
	std_output_total[15]=total_std_requirement[15]
	std_output_total[16]=std_snf
	std_output_total[17]=total_std_requirement[17]


	#endregion

	#region TM

	cream_tm_production[13]=cream_tm_production_year
	cream_tm_production[14] = cream_fat
	cream_tm_production[15] = (cream_fat*cream_tm_production_year)/100
	cream_tm_production[16]=cream_snf
	cream_tm_production[17]=(cream_snf*cream_tm_production_year)/100


	smp_tm_production[13]=smp_tm_production_year
	smp_tm_production[14] = 0
	smp_tm_production[15] = 0
	smp_tm_production[16] = smp_snf
	smp_tm_production[17] = (smp_tm_production_year*smp_snf)/100

	tm_input_total[13]=wm_tm_production_year+cream_std_production_year+smp_tm_production_year
	tm_input_total[14]=0
	tm_input_total[15]=wm_tm_production[15]+cream_std_production[15]
	tm_input_total[16] = smp_snf
	tm_input_total[17] = wm_tm_production[17] + cream_std_production[17]+smp_std_production[17]



	total_tm_requirement[13]=total_tm_requirement_year
	total_tm_requirement[14]=tm_fat
	total_tm_requirement[15]=(total_tm_requirement_year*tm_fat)/100
	total_tm_requirement[16] = tm_snf
	total_tm_requirement[17] = (total_tm_requirement_year * tm_snf) / 100



	tm_output_total[13]=total_tm_requirement_year
	tm_output_total[14]=tm_fat
	tm_output_total[15] =total_tm_requirement[15]
	tm_output_total[16]=tm_snf
	tm_output_total[17] = total_tm_requirement[17]



	#endregion

	#region Jersey
	cream_Jersey_production[13] = cream_Jersey_production_year
	cream_Jersey_production[14] = cream_fat
	cream_Jersey_production[15] = (cream_Jersey_production_year*cream_fat)/100
	cream_Jersey_production[16] = cream_snf
	cream_Jersey_production[17] = (cream_Jersey_production_year*cream_snf)/100




	smp_Jersey_production[13] = smp_Jersey_production_year
	smp_Jersey_production[14]=0
	smp_Jersey_production[15] = 0
	smp_Jersey_production[16] = smp_snf
	smp_Jersey_production[17] = (smp_snf*smp_Jersey_production_year)/100





	Jersey_input_total[13] = wm_Jersey_production_year + cream_Jersey_production_year + smp_Jersey_production_year
	Jersey_input_total[14]=0
	Jersey_input_total[15] = wm_Jersey_production[15]+cream_Jersey_production[15]
	Jersey_input_total[16] = 0
	Jersey_input_total[17] = wm_Jersey_production[17] + cream_Jersey_production[17]+smp_Jersey_production[17]


	total_Jersey_requirement[13] = total_Jersey_requirement_year
	total_Jersey_requirement[14]=jersey_fat
	total_Jersey_requirement[15] = (total_Jersey_requirement_year*jersey_fat)/100
	total_Jersey_requirement[16]=jersey_snf
	total_Jersey_requirement[17] = (total_Jersey_requirement_year*jersey_snf)/100




	Jersey_output_total[13] = total_Jersey_requirement_year
	Jersey_output_total[14] = 0
	Jersey_output_total[15] =total_Jersey_requirement[15]
	Jersey_output_total[16] = 0
	Jersey_output_total[17] = total_Jersey_requirement[17]


	#endregion

	#region HTM
	cream_htm_production[13] = cream_htm_production_year
	cream_htm_production[14]=cream_fat
	cream_htm_production[15]=(cream_htm_production_year*cream_fat)/100
	cream_htm_production[16]=cream_snf
	cream_htm_production[17] = (cream_htm_production_year * cream_snf) / 100



	smp_htm_production[13] = smp_htm_production_year
	smp_htm_production[14]=0
	smp_htm_production[15]=0
	smp_htm_production[16]=smp_snf
	smp_htm_production[17] = (smp_snf*smp_htm_production_year)/100

	htm_input_total[13] = wm_htm_production_year + cream_htm_production_year + smp_htm_production_year
	htm_input_total[14]=0
	htm_input_total[15]=wm_htm_production[15]+cream_htm_production[15]
	htm_input_total[16]=0
	htm_input_total[17] = wm_htm_production[17] + cream_htm_production[17]



	total_htm_requirement[13] = total_htm_requirement_year
	total_htm_requirement[14] = htm_fat
	total_htm_requirement[15]=(total_htm_requirement_year*htm_fat)/100
	total_htm_requirement[16] = htm_snf
	total_htm_requirement[17] = (total_htm_requirement_year * htm_snf) / 100




	htm_output_total[13] = total_htm_requirement_year
	htm_output_total[14]=htm_fat
	htm_output_total[15]=total_htm_requirement[15]
	htm_output_total[16] = htm_snf
	htm_output_total[17] = total_htm_requirement[17]

	#endregion

	# region DTM
	cream_dtm_production[13] = cream_dtm_production_year
	cream_dtm_production[14] = cream_fat
	cream_dtm_production[15] = (cream_dtm_production_year*cream_fat)/100
	cream_dtm_production[16] = cream_snf
	cream_dtm_production[17] = (cream_dtm_production_year * cream_snf) / 100




	smp_dtm_production[13] = smp_dtm_production_year
	smp_dtm_production[14] = 0
	smp_dtm_production[15] = 0
	smp_dtm_production[16] = smp_snf
	smp_dtm_production[17] = (smp_dtm_production_year*smp_snf)/100


	dtm_input_total[13] = wm_dtm_production_year + cream_dtm_production_year + smp_dtm_production_year
	dtm_input_total[14]=0
	dtm_input_total[15] =wm_dtm_production[15]+ cream_dtm_production[15]
	dtm_input_total[16] = 0
	dtm_input_total[17] = wm_dtm_production[17] + cream_dtm_production[17]



	total_dtm_requirement[13] = total_dtm_requirement_year
	total_dtm_requirement[14]=dtm_fat
	total_dtm_requirement[15]=(total_dtm_requirement_year*dtm_fat)/100
	total_dtm_requirement[16] = dtm_snf
	total_dtm_requirement[17] = (total_dtm_requirement_year * dtm_snf) / 100



	dtm_output_total[13] = total_dtm_requirement_year
	dtm_output_total[14]=dtm_fat
	dtm_output_total[15]=total_dtm_requirement[15]
	dtm_output_total[16] = dtm_snf
	dtm_output_total[17] =total_dtm_requirement[17]
	# endregion

	# region SM
	cream_sm_production[13] = cream_sm_production_year
	cream_sm_production[14] = cream_fat
	cream_sm_production[15] = (cream_sm_production_year*cream_fat)/100
	cream_sm_production[16] = cream_snf
	cream_sm_production[17] = (cream_sm_production_year * cream_snf) / 100



	smp_sm_production[13] = smp_sm_production_year
	smp_sm_production[14]=0
	smp_sm_production[15] = 0
	smp_sm_production[16] = smp_snf
	smp_sm_production[17] = (smp_sm_production_year*smp_snf)/100



	sm_input_total[13] = wm_sm_production_year + cream_sm_production_year + smp_sm_production_year
	sm_input_total[14]=0
	sm_input_total[15] =wm_sm_production[15]+cream_sm_production[15]
	sm_input_total[16] = 0
	sm_input_total[17] = wm_sm_production[17] + cream_sm_production[17] + smp_sm_production[17]




	total_sm_requirement[13] = total_sm_requirement_year
	total_sm_requirement[14]=sm_fat
	total_sm_requirement[15] = (total_sm_requirement_year*sm_fat)/100
	total_sm_requirement[16] = sm_snf
	total_sm_requirement[17] = (total_sm_requirement_year * sm_snf) / 100




	sm_output_total[13] = total_sm_requirement_year
	sm_output_total[14]=sm_fat
	sm_output_total[15]=total_sm_requirement[15]
	sm_output_total[16] = sm_snf
	sm_output_total[17] = total_sm_requirement[17]



	# endregion

	#region RC
	cream_rc_requirement[13]=cream_rc_requirement_year
	cream_rc_requirement[14] = cream_fat
	cream_rc_requirement[15] = (cream_rc_requirement_year*cream_fat)/100
	cream_rc_requirement[16] = cream_snf
	cream_rc_requirement[17] = (cream_rc_requirement_year * cream_snf) / 100


	smp_rc_smp_requirement[13]=smp_rc_smp_requirement_year
	smp_rc_smp_requirement[14] = 0
	smp_rc_smp_requirement[15] = 0
	smp_rc_smp_requirement[16] = smp_snf
	smp_rc_smp_requirement[17] = (smp_rc_smp_requirement_year*smp_snf)/100


	smp_rc_wmp_requirement[13]=smp_rc_wmp_requirement_year
	smp_rc_wmp_requirement[14] = 0
	smp_rc_wmp_requirement[15] = 0
	smp_rc_wmp_requirement[16] = smp_snf
	smp_rc_wmp_requirement[17] = (smp_rc_wmp_requirement_year*smp_snf)/100



	water_rc_smp_requirement[13]=water_rc_smp_requirement_year
	water_rc_smp_requirement[14] = 0
	water_rc_smp_requirement[15] = 0
	water_rc_smp_requirement[16] = 0
	water_rc_smp_requirement[17] = 0




	water_rc_wmp_requirement[13]=water_rc_wmp_requirement_year
	water_rc_wmp_requirement[14] = 0
	water_rc_wmp_requirement[15] = 0
	water_rc_wmp_requirement[16] = 0
	water_rc_wmp_requirement[17] = 0

	wmp_rc_wmp_requirement[13]=wmp_rc_wmp_requirement_year
	wmp_rc_wmp_requirement[14]=wmp_fat
	wmp_rc_wmp_requirement[15]=(wmp_rc_wmp_requirement_year*wmp_fat)/100
	wmp_rc_wmp_requirement[16] = wmp_snf
	wmp_rc_wmp_requirement[17] = (wmp_rc_wmp_requirement_year * wmp_snf) / 100


	rc_input_total[13]=cream_rc_requirement_year+smp_rc_smp_requirement_year+smp_rc_wmp_requirement_year+water_rc_smp_requirement_year+water_rc_wmp_requirement_year+wmp_rc_wmp_requirement_year
	rc_input_total[14]=0
	rc_input_total[15]=cream_rc_requirement[15]+wmp_rc_wmp_requirement[15]
	rc_input_total[16] =0
	rc_input_total[17] = cream_rc_requirement[17] +smp_rc_smp_requirement[17]+smp_rc_wmp_requirement[17] +wmp_rc_wmp_requirement[17]

	rc_output_total[13]=wm_reconstitution_year
	rc_output_total[14]=wm_fat
	rc_output_total[15] = wm_reconstitution_list[15]
	rc_output_total[16] = wm_snf
	rc_output_total[17] = wm_reconstitution_list[17]


	#endregion

	#region CREAM TALLY
	cream_purchase_list[13]=cream_purchase_year
	cream_purchase_list[14]=cream_fat
	cream_purchase_list[15] = (cream_purchase_year*cream_fat)/100
	cream_purchase_list[16] = cream_snf
	cream_purchase_list[17] = (cream_purchase_year * cream_snf) / 100


	cream_surplus_csm[13]=cream_surplus_csm_year
	cream_surplus_csm[14] = cream_fat
	cream_surplus_csm[15] = (cream_surplus_csm_year*cream_fat)/100
	cream_surplus_csm[16] = cream_snf
	cream_surplus_csm[17] = (cream_surplus_csm_year*cream_snf)/100


	cream_input_total[13]=cream_purchase_year+cream_stockin_year+cream_Jersey_production_year+cream_tm_production_year+cream_htm_production_year+cream_dtm_production_year+cream_sm_production_year+cream_surplus_csm_year
	cream_input_total[14]=cream_fat
	cream_input_total[15]=cream_purchase_list[15]+cream_stock_in_fat_year+cream_Jersey_production[15]+cream_tm_production[15]+cream_htm_production[15]+cream_dtm_production[15]+cream_sm_production[15]+cream_surplus_csm[15]
	cream_input_total[16] = cream_snf
	cream_input_total[17] = cream_purchase_list[17] + cream_stock_in_snf_year + cream_Jersey_production[17] +cream_tm_production[17] + cream_htm_production[17] + cream_dtm_production[17] +cream_sm_production[17] + cream_surplus_csm[17]




	cream_requirement_product[13]=cream_requirement_product_year
	cream_requirement_product[14]=cream_fat
	cream_requirement_product[15]=(cream_requirement_product_year*cream_fat)/100
	cream_requirement_product[16] = cream_snf
	cream_requirement_product[17] = (cream_requirement_product_year * cream_snf) / 100


	cream_sale_list[13]=cream_sale_list_year
	cream_sale_list[14]=cream_fat
	cream_sale_list[15]=(cream_sale_list_year*cream_fat)/100
	cream_sale_list[16] = cream_snf
	cream_sale_list[17] = (cream_sale_list_year * cream_snf) / 100


	cream_output_total[13]=cream_std_production_year+cream_rc_requirement_year+cream_stockout_year+cream_sale_list_year
	cream_output_total[14]=cream_fat
	cream_output_total[15]=cream_std_production[15]+cream_rc_requirement[15]+cream_stock_out_fat_year+cream_sale_list[15]
	cream_output_total[16] = cream_snf
	cream_output_total[17] = cream_std_production[17] + cream_rc_requirement[17] + cream_stock_out_snf_year +cream_sale_list[17]

	#endregion

	#region SMP TALLY
	smp_purchase_list[13]=smp_purchase_list_year
	smp_purchase_list[14] = 0
	smp_purchase_list[15] = 0
	smp_purchase_list[16] = smp_snf
	smp_purchase_list[17] = (smp_purchase_list_year*smp_snf)/100

	smp_from_conversion[13]=smp_from_conversion_year
	smp_from_conversion[14] = 0
	smp_from_conversion[15] = 0
	smp_from_conversion[16] = smp_snf
	smp_from_conversion[17] = (smp_from_conversion_year*smp_snf)/100




	smp_input_total[13]=smp_purchase_list_year+smp_from_conversion_year
	smp_input_total[14]=0
	smp_input_total[15] = 0
	smp_input_total[16] = smp_snf
	smp_input_total[17] = smp_purchase_list[17]+smp_from_conversion[17]


	smp_requirement[13]=smp_requirement_year
	smp_requirement[14] = 0
	smp_requirement[15] = 0
	smp_requirement[16] =smp_snf
	smp_requirement[17] = (smp_requirement_year*smp_snf)/100




	smp_sale_list[13]=smp_sale_list_year
	smp_sale_list[14]=0
	smp_sale_list[15] = 0
	smp_sale_list[16] = smp_snf
	smp_sale_list[17] = (smp_sale_list_year*smp_snf)/100




	smp_output_total[13]=smp_requirement_year+smp_sale_list_year
	smp_output_total[14]=0
	smp_output_total[15]=0
	smp_output_total[16] = smp_snf
	smp_output_total[17] = smp_requirement[17]+smp_sale_list[17]


	#endregion

	#region CSM TALLY
	csm_snf=scsmCalculation()
	csm_produced[13]=csm_produced_year
	csm_produced[14]=wm_fat
	csm_produced[15] = (csm_produced_year*wm_fat)/100
	csm_produced[16] = wm_snf
	csm_produced[17] = (csm_produced_year * wm_snf) / 100


	csm_input_total[13]=csm_produced_year
	csm_input_total[14]=wm_fat
	csm_input_total[15] =csm_produced[15]
	csm_input_total[16] = wm_snf
	csm_input_total[17] = csm_produced[17]






	csm_sale_list[13]=csm_sale_list_year
	csm_sale_list[14] = csm_fat
	csm_sale_list[15] = (csm_sale_list_year*csm_fat)/100
	csm_sale_list[16] = csm_snf
	csm_sale_list[17] = (csm_sale_list_year * csm_snf) / 100



	csm_for_conversion[13]=csm_for_conversion_year
	csm_for_conversion[14]=csm_fat
	csm_for_conversion[15]=(csm_for_conversion_year*csm_fat)/100
	csm_for_conversion[16] = csm_snf
	csm_for_conversion[17] = (csm_for_conversion_year * csm_snf) / 100


	csm_output_total[13]=cream_surplus_csm_year+csm_sale_list_year+csm_for_conversion_year
	csm_output_total[14]=0
	csm_output_total[15] = cream_surplus_csm[15]+csm_sale_list[15]+csm_for_conversion[15]
	csm_output_total[16] = 0
	csm_output_total[17] = cream_surplus_csm[17] + csm_sale_list[17] + csm_for_conversion[17]


	#endregion


	#endregion


	return render(request, 'prediction/ReportAnnualMAT.html',{'wm_purchase_list':wm_purchase_list,'wm_reconstitution_list':wm_reconstitution_list
			,'wm_requirement_product':wm_requirement_product,'wm_stock_out_transfer_list':wm_stock_out,'wm_procurement_list':wm_procurement_list
,'wm_Jersey_production':wm_Jersey_production,'wm_tm_production':wm_tm_production,'wm_htm_production':wm_htm_production,'wm_std_production':wm_std_production
,'wm_dtm_production':wm_dtm_production,'wm_sm_production':wm_sm_production,'wm_surplus_sale_list':wm_surplus_sale_list
		,'month':month_list,'wm_stock_in_transfer_list':wm_stock_in,'wm_input_total':wm_input_total,'wm_surplus_csm':wm_surplus_csm
,'wm_output_total':wm_output_total,'cream_std_production':cream_std_production,'smp_std_production':smp_std_production
,'std_input_total':std_input_total,'total_std_requirement':total_std_requirement,'std_output_total':std_output_total
,'cream_tm_production':cream_tm_production,'smp_tm_production':smp_tm_production,'tm_input_total':tm_input_total,'total_tm_requirement':total_tm_requirement
,'tm_output_total':tm_output_total,'cream_Jersey_production':cream_Jersey_production,'smp_Jersey_production':smp_Jersey_production
,'Jersey_input_total':Jersey_input_total,'total_Jersey_requirement':total_Jersey_requirement,'Jersey_output_total':Jersey_output_total
,'cream_htm_production':cream_htm_production,'smp_htm_production':smp_htm_production,'total_htm_requirement':total_htm_requirement
,'htm_input_total':htm_input_total,'htm_output_total':htm_output_total,'cream_dtm_production':cream_dtm_production,'smp_dtm_production':smp_dtm_production
,'total_dtm_requirement':total_dtm_requirement,'dtm_input_total':dtm_input_total,'dtm_output_total':dtm_output_total
,'cream_sm_production':cream_sm_production,'smp_sm_production':smp_sm_production,'total_sm_requirement':total_sm_requirement,
'sm_input_total':sm_input_total,'sm_output_total':sm_output_total,'cream_rc_requirement':cream_rc_requirement,'smp_rc_smp_requirement':smp_rc_smp_requirement
,'smp_rc_wmp_requirement':smp_rc_wmp_requirement,'water_rc_smp_requirement':water_rc_smp_requirement,'water_rc_wmp_requirement':water_rc_wmp_requirement,
 'wmp_rc_wmp_requirement':wmp_rc_wmp_requirement,'rc_input_total':rc_input_total,'rc_output_total':rc_output_total,'cream_purchase_list':cream_purchase_list
,'cream_stock_in':cream_stock_in,'cream_surplus_csm':cream_surplus_csm,'cream_input_total':cream_input_total,'cream_requirement_product':cream_requirement_product
,'cream_stock_out':cream_stock_out,'cream_sale_list':cream_sale_list,'cream_output_total':cream_output_total,'smp_purchase_list':smp_purchase_list,
'smp_from_conversion':smp_from_conversion,'smp_input_total':smp_input_total,'smp_requirement':smp_requirement,'smp_sale_list':smp_sale_list
,'smp_output_total':smp_output_total,'csm_produced':csm_produced,'csm_input_total':csm_input_total,'csm_sale_list':csm_sale_list,'csm_for_conversion':csm_for_conversion
,'csm_output_total':csm_output_total})
@login_required
def reportFinanceYear(request):


	categoryList=Category.objects.all()
	diaryList=Diary.objects.all()
	wm_procurement_list=OrderedDict()
	category_sale_list=OrderedDict()





	for diary in diaryList:
		wm_procurement_diary=0
		for month in MONTHS.items():

			try:

				wm_procurement_obj=ActualWMProcurement.objects.get(diary=diary,month=month[0])
				wm_procurement_month=wm_procurement_obj.targetAmount
			except Exception as e:
				print  "Exception handeld in reportFinanceYear wm procurement fetching failed"
				wm_procurement_month=0

			wm_procurement_diary+=wm_procurement_month
		wm_procurement_list[diary.name] = wm_procurement_diary

	for category in categoryList:

		category_diary_sale=[]
		for diary in diaryList:
			salesum_category = 0
			for month in MONTHS.items():

				saledetails = ActualSale.objects.filter(
					product__in=(Product.objects.filter(category=category)).values('code'), month=month[0], diary=diary)

				for sale in saledetails:
					salesum_category += sale.targetRevenue
			category_sale_item={'diary':diary.name,'amount':salesum_category}
			category_diary_sale.append(category_sale_item)
		category_sale_list[category.name]=category_diary_sale




	wm_purchase_monthlist=OrderedDict()
	cream_purchase_monthlist=OrderedDict()
	smp_purchase_monthlist=OrderedDict()
	for month_item in MONTHS.items():

		issue_wm = Issue.objects.get(name='WM')

		issue_cream = Issue.objects.get(name='CREAM')
		issue_smp = Issue.objects.get(name='SMP')

		month=month_item[0]







		resultitem = []

		cream_requirement_list = []

		smp_requirement_list = []

		wmp_requirement_list = []
		shortage_list = OrderedDict()
		surplus_list = OrderedDict()

		fwm = issue_wm.fat

		diary_list = Diary.objects.all()
		total_requirement_diary_cpd = 0
		wm_requirement_product_month=0


		for diary in diary_list:

			ret_month, month_issue_requirement_sales_wm = totalIssueRequirement(month, diary, issue_wm)

			m, issueasproduct_wm = IssueasProduct(month, diary, issue_wm)


			wm_requirement_product_month += month_issue_requirement_sales_wm-issueasproduct_wm

			ret_month, month_issue_requirement_sales_cream = totalIssueRequirement(month, diary, issue_cream)



			ret_month, month_issue_requirement_sales_smp = totalIssueRequirement(month, diary, issue_smp)




			month_requirement_for_milk_issue_production_wm = 0
			month_requirement_for_milk_issue_production_cream = 0
			month_requirement_for_milk_issue_production_smp = 0
			type2_issue_list = Issue.objects.filter(type='2')

			for issue_item in type2_issue_list:



				try:

					issue_ret_month, month_issue_requirement = totalIssueRequirement(month, diary, issue_item)




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
					print "Exception handled reportAnnual in line no 4695"

				requirement_to_produce_milk_issue_wm = month_issue_requirement * composition_ratio_derived_wm
				month_requirement_for_milk_issue_production_wm += requirement_to_produce_milk_issue_wm

				requirement_to_produce_milk_issue_cream = month_issue_requirement * composition_ratio_derived_cream
				month_requirement_for_milk_issue_production_cream += requirement_to_produce_milk_issue_cream

				requirement_to_produce_milk_issue_smp = month_issue_requirement * composition_ratio_derived_smp
				month_requirement_for_milk_issue_production_smp += requirement_to_produce_milk_issue_smp

			total_month_requirement_wm = month_requirement_for_milk_issue_production_wm + month_issue_requirement_sales_wm

			total_month_requirement_cream = month_requirement_for_milk_issue_production_cream + month_issue_requirement_sales_cream

			total_month_requirement_smp = month_requirement_for_milk_issue_production_smp + month_issue_requirement_sales_smp





			total_month_procurement = 0
			try:
				Awm_obj = ActualWMProcurement.objects.get(diary=diary, month=month)

				total_month_procurement = Awm_obj.targetProcurement


			except Exception as e:
				print "Exception handled reportAnnual in line 4724"

			difference = total_month_procurement - total_month_requirement_wm

			if difference != 0:
				type_of_difference = ""
				if difference >= 0:
					type_of_difference = "Surplus"
					surplus_list[diary.name] = difference
				else:
					type_of_difference = "Shortage"
					difference = difference * -1
					shortage_list[diary.name] = difference



			if "CPD" == diary.id:
				total_requirement_diary_cpd = total_month_requirement_wm

			cream_requirement_item = {"month": MONTHS[month], "diary": diary,
									  "total_cream_used": 0 - total_month_requirement_cream, "type": "Surplus"}
			cream_requirement_list.append(cream_requirement_item)
			smp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_smp_used": 0 - total_month_requirement_smp, "type": "Sale"}
			smp_requirement_list.append(smp_requirement_item)

			wmp_requirement_item = {"month": MONTHS[month], "diary": diary,
									"total_wmp_used": 0, "type": "Sale"}
			wmp_requirement_list.append(wmp_requirement_item)




		after_transfer_diary, inter_stock_transfer = interMilkTransfer(shortage_list, surplus_list,
																	   total_requirement_diary_cpd, diary_list)
		after_wm_balancing_diarylist,wm_purchase_list = wmBalancingReportFinance(after_transfer_diary, month)

		wm_purchase_monthlist[month]=wm_purchase_list


		shortage_list_cream = OrderedDict()
		surplus_list_cream = OrderedDict()

		cream_list = []
		for item_cream in cream_requirement_list:

			for item in after_wm_balancing_diarylist:

				if item_cream['diary'].name == item['diary']:
					requirement = item_cream['total_cream_used'] * (-1)
					item_cream['total_cream_used'] = 0 - (requirement + item['cream_used_csm'] + item['cream_used_smp'])

				if item_cream['total_cream_used'] < 0:
					item_cream['type'] = "Shortage"

					cream_used = item_cream['total_cream_used'] * (-1)
					shortage_list_cream[item_cream['diary']] = cream_used * (-1)


				elif item_cream['total_cream_used'] > 0:
					item_cream['type'] = "Surplus"
					surplus_list_cream[item_cream['diary']] = item_cream['total_cream_used']
			if item_cream['total_cream_used'] != 0:
				if item_cream['total_cream_used'] < 0:
					item_cream['total_cream_used'] = item_cream['total_cream_used'] * (-1)
				cream_list.append(item_cream)
		smp_after_transfer = []
		smp_purchase_list=[]
		for item_smp in smp_requirement_list:

			for item in after_wm_balancing_diarylist:
				if item_smp['diary'].name == item['diary']:
					requirement = item_smp['total_smp_used'] * (-1)
					item_smp['total_smp_used'] = 0 - (
					requirement + item['smp_used_smp'] + item['smp_used_wmp'] - item['converted_smp'])

				if item_smp['total_smp_used'] < 0:
					item_smp['type'] = "Purchase"

					used = item_smp['total_smp_used'] * (-1)



					item_smp['total_smp_used'] = used

				elif item_smp['total_smp_used'] > 0:
					item_smp['type'] = "Sale"

			if item_smp['type'] == "Sale":
				try:
					sale_rate = GeneralCalculation.objects.get(code='14').value


					smp_item = {
						'transaction': 'SMP Sold:' + str(item_smp['total_smp_used']) + " ,Amount:" + str(
							item_smp['total_smp_used'] * sale_rate), 'diary': item_smp['diary'].name}

				except Exception as e:
					print "Exception handled At 4819"
			else:
				try:
					rate = GeneralCalculation.objects.get(code='13').value
					smp_purchase_amount=item_smp['total_smp_used'] * rate


					smp_item = {'transaction': 'SMP Purchased:' + str(
						item_smp['total_smp_used']) + " ,Amount:" + str(
						smp_purchase_amount), 'diary': item_smp['diary'].name}

					smp_purchase_item={'diary': item_smp['diary'].name,'Amount':smp_purchase_amount}


				except Exception as e:
					print "Exception handled At 4830"
			if item_smp['total_smp_used'] != 0:
				smp_after_transfer.append(smp_item)
		wmp_after_transfer = []
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
						item_wmp['total_wmp_used']) + " ,Amount:" + str(
						item_wmp['total_wmp_used'] * sale_rate), 'diary': item_wmp['diary'].name}

				except Exception as e:
					print "Exception handled At 4858"
			else:
				try:
					rate = GeneralCalculation.objects.get(code='11').value
					wmp_item = {'transaction': 'WMP Purchased:' + str(
						item_wmp['total_wmp_used']) + " ,Amount:" + str(
						item_wmp['total_wmp_used'] * rate), 'diary': item_wmp['diary'].name}

				except Exception as e:
					print "Exception handled At 4867"
			if item_wmp['total_wmp_used'] != 0:
				wmp_after_transfer.append(wmp_item)

		after_cream_transfer_diary, inter_stock_transfer_cream = interCreamTransfer(shortage_list_cream, surplus_list_cream,
																					diary_list)

		after_cream_balancing_diarylist,cream_purchase_list= creamBalancingReportFinance(after_cream_transfer_diary)
		cream_purchase_monthlist[month]=cream_purchase_list

		smp_purchase_monthlist[month]=smp_purchase_list



	# for diary in diaryList:
    #
	# 	for purchase in wm_purchase_monthlist:
	# 		print str(purchase[])
























	return render(request, 'prediction/ReportFinance.html',{'diaryList':diaryList,'wm_procurement_list':wm_procurement_list,
															'category_sale_list':category_sale_list})










