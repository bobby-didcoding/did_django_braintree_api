from django.db import models
from django.contrib.auth.models import User

class Invoicing(models.Model):

	timestamp = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	tran_id = models.CharField(max_length=100)
	amount = models.IntegerField()
	
	def __str__(self):
		return f'{self.user}'