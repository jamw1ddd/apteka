from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Medicine, MedicineHistory, Patient

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role','place','who',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role','place', 'who',)}),
    )
    list_display = ('username', 'email', 'role', 'is_staff','place', 'who')


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Medicine)
admin.site.register(MedicineHistory)
admin.site.register(Patient)
