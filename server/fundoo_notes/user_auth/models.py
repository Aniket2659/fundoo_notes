from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    This model replaces the default username-based authentication with email-based authentication
    and includes additional fields for user verification and phone number.

    Attributes:
        email (EmailField): The email field, used as the unique identifier for authentication.
        is_verified (BooleanField): A field indicating whether the user's email has been verified.
        phone_number (CharField): An optional field to store the user's phone number, with a maximum length of 15 characters.
        USERNAME_FIELD (str): Specifies the field to be used as the unique identifier for authentication.
        REQUIRED_FIELDS (list): A list of fields that are required when creating a user via the createsuperuser command.
    """

    email = models.EmailField(unique=True)  # unique identifier
    is_verified = models.BooleanField(default=False)  # email verification status
    phone_number = models.CharField(max_length=15, unique=True, null=True)  # extra field

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        """
        String representation of the User model.

        Returns:
            str: The user's email.
        """
        return self.email



class Log(models.Model):
    method = models.CharField(max_length=20, null=False)
    url = models.TextField(null=False)
    count = models.IntegerField(default=1)

    class Meta:
        db_table='log'

    def __str__(self):
        return f"{self.method} {self.url} - {self.count}"

