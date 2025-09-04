from django.contrib.auth.models import AbstractUser
from django.db import models
from decimal import Decimal

class Place(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Joy"
        verbose_name_plural = "Joylar"

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
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('---', '---'),
        ('tablet', 'Tabletkalar'),
        ('syrup', 'Sirop'),
        ('vitamin', 'Vitamin'),
        ('inhaler', 'Ingalator'),
    ]
    
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='---',blank=True,null=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)  # Quti narxi
    box_quantity = models.PositiveIntegerField(default=1)  # Qutidagi dona soni
    quantity = models.PositiveIntegerField(default=0)  # Qutining soni (omborda nechta quti bor)
    extra_units = models.PositiveIntegerField(default=0) # Qutilardan tashqari qolgan donalar

    expiry_date = models.DateField(blank=True, null=True)
    owner = models.ForeignKey("CustomUser", on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    place = models.ForeignKey("Place", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def unit_price(self):
        """1 dona narxi"""
        if self.box_quantity > 0:
            return self.price / Decimal(self.box_quantity)
        return self.price

    @property
    def total_units(self):
        """Jami dona: qutilar * dona_per_quti + extra_units"""
        return self.quantity * self.box_quantity + (self.extra_units or 0)

    @property
    def total_boxes(self):
        """Butun qutilar soni (quantity maydoni)"""
        return self.quantity
    
    @property
    def remaining_units(self):
        """Qutilardan tashqari qolgan donalar (raqam)"""
        return self.extra_units or 0
    
    @property
    def remaining_display(self):
        """
        Chiroyli format: misol: "91 quti (5 dona)"
        - Agar qutida faqat 1 dona bo‘lsa, faqat quti ko‘rinadi.
        """
        if self.box_quantity <= 0:
            return f"{self.total_units} dona"

        # Agar qutida 1 dona bo‘lsa, donani ko‘rsatmaslik
        if self.box_quantity == 1:
            return f"{self.total_units} quti"

        full_boxes, remainder = divmod(self.total_units, self.box_quantity)

        if full_boxes and remainder:
            return f"{full_boxes} quti ({remainder} dona)"
        if full_boxes and not remainder:
            return f"{full_boxes} quti"
        return f"{remainder} dona"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dori"
        verbose_name_plural = "Dorilar"
    
class Patient(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Bemor"
        verbose_name_plural = "Bemorlar"
    
class MedicineHistory(models.Model):
    ACTION_CHOICES = (
        ('added', 'Qo‘shildi'),
        ('transferred', 'Chiqarildi'),
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # kim amalga oshirgan
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, related_name='received_medicine')
    to_patient = models.ForeignKey(Patient, on_delete=models.CASCADE, blank=True, null=True, related_name="received_medicines")  # CustomUser emas # agar chiqarilgan bo‘lsa
    quantity = models.IntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    to_place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_action_display()} - {self.medicine.name} ({self.quantity})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Dori tarixi"
        verbose_name_plural = "Dori tarixi"

class PatientMedicine(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    
    # Quti va dona alohida saqlanadi
    boxes_given = models.PositiveIntegerField(default=0)
    units_given = models.PositiveIntegerField(default=0)
    
    prescribed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    @property
    def quantity(self):
        # jami dona
        return self.boxes_given * self.medicine.box_quantity + self.units_given

    @property
    def display_quantity(self):
        # Agar quti bo'lmasa, faqat dona ko'rsatadi
        if self.boxes_given > 0:
            return f"{self.boxes_given} quti + {self.units_given} dona"
        return f"{self.units_given} dona"

    @property
    def unit_price(self):
        # 1 dona narxi
        return self.medicine.price / self.medicine.box_quantity

    @property
    def total_price(self):
        if self.boxes_given > 0:
            return self.medicine.price * self.boxes_given + self.units_given * self.unit_price
        return self.units_given * self.unit_price

    def __str__(self):
        return f"{self.patient.name} — {self.medicine.name}"
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Chek"
        verbose_name_plural = "Cheklar"
