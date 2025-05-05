from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory
from factory.faker import Faker

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker("user_name")
    email = Faker("email")
