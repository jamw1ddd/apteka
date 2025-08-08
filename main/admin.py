from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Medicine, MedicineHistory, Patient, PatientMedicine, Place

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role', 'place', 'who',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role', 'place', 'who',)}),
    )

    list_display = ('username', 'email', 'role', 'is_staff', 'get_places', 'who')

    def get_places(self, obj):
        return ", ".join([p.name for p in obj.place.all()])

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Medicine)
admin.site.register(MedicineHistory)
admin.site.register(Patient)
admin.site.register(PatientMedicine)
admin.site.register(Place)
