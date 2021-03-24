from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
import json

from api.mixins import (
	gateway,
	BraintreeAccount,
	BraintreePayment,
	BraintreeData,
	generate_client_token,
	transact,
	find_transaction,
	)

from api.models import (
	Invoicing
	)

# import braintree



'''
Cart view for Braintree payment
'''
@login_required
def cart(request):

	user = request.user
	agent_id = user.userprofile.agent_id
	
	#do i need to do this everytime??
	braintree_client_token = gateway.client_token.generate({"customer_id": agent_id})

	context = {
		"braintree_client_token": braintree_client_token,
	}
	return render(request,'api/cart.html', context)


'''
AJAX function to handle a Braintree payment
'''
@login_required
def payment(request):

	if request.method == "POST":

		user = request.user
		token = request.POST.get('braintreeToken',None)
		card_id = request.POST.get("card_id", None)
		paymentMethodNonce = request.POST.get("paymentMethodNonce", None)
		description = request.POST.get("description", None)
		currency = request.POST.get("currency", None)
		set_default = request.POST.get("set_default", None)

		amount = request.POST.get('amount')

		agent_id = user.userprofile.agent_id

		if not agent_id:
			BraintreeAccount(request.user).agent()

		payment = BraintreePayment(
			user=user,
			agent_id=agent_id,
			token=token,
			card_id=card_id,
			amount=amount,
			description = description,
			currency=currency,
			set_default=set_default
			).create()

		if payment["message"] == "Perfect":

			invoice = Invoicing(
				user = user,
				tran_id = payment["tran_id"],
				amount = float(amount)
				)
			invoice.save()
			user = user

			return HttpResponse(
					json.dumps({"result": "okay"}),
					content_type="application/json"
					)
		else:
			return HttpResponse(
					json.dumps({"result": "error", "message":payment["message"] }),
					content_type="application/json"
					)
	else:
		return HttpResponse(
			json.dumps({"result": "error"}),
			content_type="application/json"
			#78325
			)

