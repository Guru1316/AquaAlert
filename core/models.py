# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

# 1. Custom User Model
# We extend Django's built-in User model to add the 'role' and 'phone_number' fields.
class CustomUser(AbstractUser):
    # Define the roles as choices
    ROLE_CHOICES = (
        ('worker', 'Health Worker'),
        ('official', 'Health Official'),
    )
    
    # We don't need a separate first/last name, username will suffice for login
    # We will use email for officials and a constructed email for workers
    email = models.EmailField(unique=True) # Ensure emails are unique
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='worker')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.username

# 2. Health Report Model
# This stores the data submitted by Health Workers.
class HealthReport(models.Model):
    # Link to the user who submitted the report
    reported_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    village = models.CharField(max_length=100)
    age_group = models.CharField(max_length=10)
    symptoms = models.JSONField()  # Stores the list of symptoms
    timestamp = models.DateTimeField(auto_now_add=True) # Automatically sets the time of creation

    def __str__(self):
        return f"Report for {self.village} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# 3. Water Quality Report Model
# This stores the simulated data from our "IoT device".
class WaterQualityReport(models.Model):
    village = models.CharField(max_length=100)
    ph = models.DecimalField(max_digits=4, decimal_places=2) # e.g., 7.50
    turbidity = models.DecimalField(max_digits=5, decimal_places=2) # e.g., 1.23 NTU
    # You can add more fields like chlorine, nitrates etc. as needed
    contaminants = models.JSONField(default=dict) # e.g., {"e-coli": "present", "arsenic": "low"}
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Water report for {self.village} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"