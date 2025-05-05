from django.contrib.auth.models import AbstractUser
from django.db import models


# Build off of the base user and add fields. This is more extensible in the future.
class User(AbstractUser):
    # email = models.EmailField(blank=True, unique=True) # override default email behavior here as you want - NOTE: email not unique by default in django
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
