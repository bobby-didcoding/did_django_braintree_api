from datetime import datetime, date, time, timedelta
from django.conf import settings
from users.models import UserProfile
from api.models import Invoicing
import braintree

gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=settings.BT_ENVIRONMENT,
        merchant_id=settings.BT_MERCHANT_ID,
        public_key=settings.BT_PUBLIC_KEY,
        private_key=settings.BT_PRIVATE_KEY
    )
)
if settings.BT_ENVIRONMENT == "sandbox":
	bt_env = braintree.Environment.Sandbox
else:
	bt_env = braintree.Environment.Production

bt_config = braintree.Configuration.configure(
		bt_env,
		merchant_id=settings.BT_MERCHANT_ID,
		public_key=settings.BT_PUBLIC_KEY,
		private_key=settings.BT_PRIVATE_KEY,
	)

def generate_client_token():
    return gateway.client_token.generate()

def transact(options):
    return gateway.transaction.sale(options)

def find_transaction(id):
    return gateway.transaction.find(id)

'''
Manages the creation of a Braintree user account
'''
class BraintreeAccount:

	def __init__(self, user):

		self.user = user

		#create Braintree account
		agent_account = gateway.customer.create({"email": self.user.username})
		agent_account_id = agent_account.customer.id

		up = self.user.userprofile
		up.agent_id = agent_account_id
		up.save()



'''
Manage payments
'''
class BraintreePayment:

	def __init__(self, *args, **kwargs):

		self.user = kwargs.get("user")
		self.agent_id = kwargs.get("agent_id")
		self.token = kwargs.get("token")
		self.amount = kwargs.get("amount")
		self.card_id = kwargs.get("card_id")
		self.description = kwargs.get("description")
		self.currency = kwargs.get("currency")
		self.set_default = kwargs.get("set_default")

	def create(self):
			
		payment_method = gateway.payment_method.create({
			"customer_id": self.agent_id,
			"payment_method_nonce": self.token,
			"options": {
				"make_default": True,
			    "verify_card": True,
			    "fail_on_duplicate_payment_method": True
			  }
		})

		customer = gateway.customer.find(self.agent_id)
		temp_list = []

		result = transact({
			'amount': self.amount,
			'customer_id': self.agent_id,
			'options': {
				"submit_for_settlement": True
			}
		})

		if result.is_success or result.transaction:
			return {
				"message": "Perfect",
				"tran_id": result.transaction.id
			}
		else:
			return {
				"message": ", ".join([ f'{x.code} - {x.message}' for x in result.errors.deep_errors]),
				"tran_id": "N/A"
			}



'''
Produces and returns a list of cards assigned to each user
'''
class BraintreeData:

	def __init__(self, user):
		self.user = user

	def invoices(self):

		agent_id = self.user.userprofile.agent_id

		# try:

		#Query user invoices
		invoices = gateway.transaction.search( 
			braintree.TransactionSearch.customer_id == agent_id
			)

		invoice_list = [
		[
			inv.id,
			inv.created_at.strftime('%d-%m-%Y'),
			"Shirt",
			inv.amount,
		] 
		for inv in invoices.items]

		if not invoice_list:
			return None
		return  invoice_list
		# except:
		# 	return None
