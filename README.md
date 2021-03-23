# did_django_braintree_api
Django project with a basic user authentication

1) cd to development directory
2) mkvirtualenv did_django_braintree_api
3) mkdir did_django_braintree_api
4) clone repository to new directory
5) pip install -r requirements.txt
6) Update settings.py with your email API information

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'XXX'
EMAIL_PORT = 'XXX'
EMAIL_USE_TLS = 'XXX'
EMAIL_HOST_USER = 'XXX'
DISPLAY_NAME = "User App demo email"
DONOT_REPLY_EMAIL_PASSWORD = 'XXX'
CURRENT_SITE = "http://localhost:8000"

if DEBUG:

    BT_ENVIRONMENT = 'sandbox'
    BT_MERCHANT_ID = 'XXX'
    BT_PUBLIC_KEY = 'XXX'
    BT_PRIVATE_KEY = 'XXX'
else:

    BT_ENVIRONMENT = 'production'
    BT_MERCHANT_ID = 'XXX'
    BT_PUBLIC_KEY = 'XXX'
    BT_PRIVATE_KEY = 'XXX'


7) python manage.py makemigrations
8) python manage.py migrate
9) python manage.py runserver
10) https://localhost:8000 - Bob's your uncle!! 

