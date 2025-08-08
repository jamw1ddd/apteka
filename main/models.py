from django.contrib.auth.models import AbstractUser
from django.db import models

class Place(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('doctor', 'Doctor'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    place = models.ManyToManyField(Place, blank=True) 
    who = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

class Medicine(models.Model):
    CATEGORY_CHOICES = [
    ('tablet', 'Tabletkalar'),
    ('syrup', 'Sirop'),
    ('vitamin', 'Vitamin'),
    ('inhaler', 'Ingalator'),
    ]
    
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100)
    weight = models.CharField(max_length=50,blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    expiry_date = models.DateField(blank=True, null=True)
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE,null=True, blank=True)

    def __str__(self):
        return self.name
    
    
class MedicineHistory(models.Model):
    ACTION_CHOICES = (
        ('added', 'Qo‘shildi'),
        ('transferred', 'Chiqarildi'),
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # kim amalga oshirgan
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, related_name='received_medicine')  # agar chiqarilgan bo‘lsa
    quantity = models.IntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    to_place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_display()} - {self.medicine.name} ({self.quantity})"
    

class Patient(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname}"
    

class PatientMedicine(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    prescribed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    

    @property
    def total_price(self):
        return self.medicine.price * self.quantity
    
    def __str__(self):
        return f"{self.patient.name}"
    