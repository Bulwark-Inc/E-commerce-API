from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def save(self, *args, **kwargs):
        """ If the user is a superuser, ensure the role is 'admin' """
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)  # Call the original save method

    def __str__(self):
        return f"{self.username} ({self.role})"