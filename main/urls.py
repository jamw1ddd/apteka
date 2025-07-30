from django.urls import path
from .views import (add_staff, employeeview, give_medicine_to_patient_view, patient_invoice_view, 
                    transfer_medicine_view, employee_list,login_view,dashboard_stats_view, 
                    doctorview,add_medicine_view,medicine_list_view,logout_view,list_patients, add_patient,
                    medicine_history_view, user_medicines_view,delete_patient
                    )

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('stats/',dashboard_stats_view, name='dashboard_stats'),
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
    path('give-medicine-to-patient/', give_medicine_to_patient_view, name='give_medicine_to_patient'),
    path('invoice/<int:patient_id>/', patient_invoice_view, name='patient_invoice'),
    path('patient/delete/<int:pk>/',delete_patient, name='delete_patient'),
]