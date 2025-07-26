from django.urls import path
from .views import (add_staff, employeeview, transfer_medicine_view, employee_list,login_view,adminview, 
                    doctorview,add_medicine_view,medicine_list_view,logout_view,list_patients, add_patient,
                    medicine_history_view, user_medicines_view,
                    )

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('adminview/', adminview, name='adminview'),
    path('doctorview/', doctorview, name='doctor'),
    path('medicine/add/', add_medicine_view, name='addmedicine'),
    path('medicine/list/', medicine_list_view, name='listmedicine'),
    path('medicine/transfer/', transfer_medicine_view, name='givemedicine'),
    path('add-staff/', add_staff, name='add_staff'),
    path('employee/', employee_list, name='employee_list'),
    path('employeeview/', employeeview, name='employee'),
    path('user/<int:user_id>/medicines/', user_medicines_view, name='user_medicines'),
    path('patients/add/', add_patient, name='addpatient'),
    path('patients/', list_patients, name='list_patients'),
    path('medicine/history/', medicine_history_view, name='medicine_history'),
]