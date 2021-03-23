from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse
from django.conf import settings
from django.http import JsonResponse
import json

from .models import (
	UserToken
	)

from .mixins import (
	FormErrors,
	RedirectParams,
	TokenGenerator,
	CreateEmail
	)

from .forms import (
	UserForm,
	UserProfileForm,
	ForgottenPasswordForm,
	AuthForm,
	RequestPasswordForm
	)

from api.mixins import (
	gateway,
	BraintreeAccount,
	BraintreeData,
	)



'''
Basic view for user sign up
'''
def sign_up(request):
	
	#redirect if user is already signed in
	if request.user.is_authenticated:
		return redirect(reverse('users:account'))

	u_form = UserForm()
	up_form = UserProfileForm()
	result = "error"
	message = "Something went wrong. Please check and try again"

	#Safe guard to stop sign up until API key is added
	if settings.BT_PRIVATE_KEY == "XXX":
		return HttpResponse(
				json.dumps({"result":result, "message": message}),
				content_type="application/json"
				)

	if request.is_ajax() and request.method == "POST":
		u_form = UserForm(data = request.POST)
		up_form = UserProfileForm(data = request.POST)
		
		#if both forms are valid, do something
		if u_form.is_valid() and up_form.is_valid():
			user = u_form.save()

			#commit = False is used as userprofile.user can not be null
			up = up_form.save(commit = False)
			up.user = user
			up.save()

			# Mark user profile as inactive until verified
			user.is_active = False
			user.email = user.username
			user.save()

			#create a Braintree account for user
			agent_id = BraintreeAccount(user)

			#create a new token
			token = TokenGenerator()
			make_token = token.make_token(user)

			#Create a usertoken object to store token
			ut = UserToken.objects.create(user=user, token = make_token)
			
			#send email verification email
			CreateEmail(
				request,
				email_account = "donotreply",
				subject = 'Verify your email',
				email = user.username,
				cc = [],
				template = "verification_email.html",
				token = make_token,
				url_safe = urlsafe_base64_encode(force_bytes(user.pk))
				)
			result = "perfect"
			message = "We have sent you an email to verify your account"
		else:
			message = FormErrors(u_form, up_form)

		return HttpResponse(
			json.dumps({"result": result, "message": message}),
			content_type="application/json"
			)
		
	context = {'u_form':u_form, 'up_form':up_form}
	return render(request, 'users/sign_up.html', context)




'''
Basic view for user sign in
'''
def sign_in(request):

	#redirect if user is already signed in
	if request.user.is_authenticated:
		return redirect(reverse('users:account'))
	
	a_form = AuthForm()
	result = "error"
	message = "Something went wrong. Please check and try again"

	if request.is_ajax() and request.method == "POST":
		a_form = AuthForm(data = request.POST)
		if a_form.is_valid():
			username = a_form.cleaned_data.get('username')
			password = a_form.cleaned_data.get('password')

			#authenticate Django built in authenticate - https://docs.djangoproject.com/en/3.1/ref/contrib/auth/
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
				message = 'You are now logged in'
				result = "perfect"

		else:
			message = FormErrors(a_form)
		
		return HttpResponse(
			json.dumps({"result": result, "message": message}),
			content_type="application/json"
			)
	context = {'a_form':a_form}

	#passes 'token_error' parameter to url to handle a error message
	token_error = request.GET.get("token_error",None)
	if token_error:
		context["token_error"] = "true"
	else:
		context["token_error"] = "false"


	return render(request, 'users/sign_in.html', context)




'''
Basic view for user sign out
'''
def sign_out(request):
	logout(request)
	return redirect(reverse('users:sign-in'))



'''
Basic view for users to request a new password
'''
def forgotten_password(request):

	rp_form = RequestPasswordForm()
	result = "error"
	message = "Something went wrong. Please check and try again"

	if request.is_ajax() and request.method == "POST":
		rp_form = RequestPasswordForm(data = request.POST)

		if rp_form.is_valid():
			
			username = rp_form.cleaned_data.get('email')
			user = User.objects.get(username = username)
			#create a new token
			token = TokenGenerator()
			make_token = token.make_token(user)
			ut = UserToken.objects.create(user=user, token = make_token, is_email = False)
			
			#send email verification email
			CreateEmail(
				request,
				email_account = "donotreply",
				subject = 'Password reset',
				email = user.username,
				cc = [],
				template = "password_email.html",
				token = make_token,
				url_safe = urlsafe_base64_encode(force_bytes(user.pk))
				)
			result = "perfect"
			message = "You will receive an email to reset your password"			
		else:
			message = FormErrors(rp_form)
		
		return HttpResponse(
			json.dumps({"result": result, "message": message}),
			content_type="application/json"
			)
	context = {'rp_form':rp_form}
	return render(request, 'users/forgotten_password.html', context)





'''
Account view for registered users
'''
@login_required
def account(request):
	
	braintree_client_token = gateway.client_token.generate({"customer_id": request.user.userprofile.agent_id})
	braintree_data = BraintreeData(request.user)

	context = {
		"braintree_client_token": braintree_client_token,
		"invoices": braintree_data.invoices(),	
	}
	#passes 'verified' parameter to url to handle a success message
	verified = request.GET.get("verified",None)
	if verified:
		context["verified"] = "true"
	else:
		context["verified"] = "false"

	return render(request,'users/account.html', context)




'''
Function view to handle verification tokens
'''
def verification(request, uidb64, token):

	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
		ut = UserToken.objects.get(user = user, token = token, is_active = True)
		email_token = ut.is_email

	except(TypeError, ValueError, OverflowError, User.DoesNotExist, UserToken.DoesNotExist):

		#user our RedirectParams function to redirect & append 'token_error' parameter to fire an error message
		return RedirectParams(url = 'users:sign-in', params = {"token_error": "true"})

	#if User & UserToken exist...
	if user and ut:

		# if the token type is_email
		if email_token:
			#activate account
			user.is_active = True
			user.save()

			#deactivate the token now that it has been used
			ut.is_active = False
			ut.save()
			
			#login the user
			login(request, user)
		
		# else the token is a password token 
		else:

			fp_form = ForgottenPasswordForm(user = user)
			result = "error"
			message = "Something went wrong. Please check and try again"

			if request.is_ajax() and request.method == "POST":
				fp_form = ForgottenPasswordForm(data = request.POST, user = user)

				if fp_form.is_valid():
					
					fp_form.save()
					login(request, user)

					#deactivate the token now that it has been used
					ut.is_active = False
					ut.save()
					message = "Your password has been updated"
					result = "perfect"
								
				else:
					message = FormErrors(rp_form)
				
				return HttpResponse(
					json.dumps({"result": result, "message": message}),
					content_type="application/json"
					)
			context = {'fp_form':fp_form, "uidb64":uidb64, "token":token}
			return render(request, 'users/verification.html', context)

	#user our RedirectParams function to redirect & append 'verified' parameter to fire a success message
	return RedirectParams(url = 'users:account', params = {"verified": "true"})


