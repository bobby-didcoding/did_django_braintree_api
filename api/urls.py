from django.conf.urls import url
from . import views


app_name = "api"
urlpatterns = [	
	url(r'^cart', views.cart, name="cart"),
	url(r'^payment', views.payment, name="payment"),
	]
