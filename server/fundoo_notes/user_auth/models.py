from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True) #unique identifier
    is_verified=models.BooleanField(default=False)

    phone_number = models.CharField(max_length=15, unique=True, null=True) # extra field
    
    USERNAME_FIELD = 'email'
    
    
    REQUIRED_FIELDS = ['username']  

    # class Meta:
    #     db_table="user"

    
    def __str__(self):
        return self.email