from django.urls import path
from .views import (add_staff, allplaces_medicine_list_view, employeeview, give_medicine_to_patient_view, 
                    list_invoices, medicine_by_place_view, medicine_update, patient_invoice_view, 
                    patient_invoice_view_by_date, transfer_medicine_view, employee_list,login_view,stats_view, 
                    doctorview,add_medicine_view,medicine_list_view,logout_view,list_patients, add_patient,
                    medicine_history_view, place_medicine_list_view,delete_patient
                    )

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('stats/',stats_view, name='dashboard_stats'),
    path('doctorview/', doctorview, name='doctor'),
    path('medicine/add/', add_medicine_view, name='addmedicine'),
    path('medicine/list/', medicine_list_view, name='listmedicine'),
    path('medicine/transfer/', transfer_medicine_view, name='givemedicine'),
    path('medicine/<int:pk>/edit/', medicine_update, name='medicine_update'),
    path('add-staff/', add_staff, name='add_staff'),
    path('employee/', employee_list, name='employee_list'),
    path('employeeview/', employeeview, name='employee'),
    path('place/<int:place_id>/medicines/',place_medicine_list_view, name='place_medicines'),
    path('patients/add/', add_patient, name='addpatient'),
    path('patients/', list_patients, name='list_patients'),
    path('medicine/history/', medicine_history_view, name='medicine_history'),
    path('give-medicine-to-patient/', give_medicine_to_patient_view, name='give_medicine_to_patient'),
    path('invoice/<int:patient_id>/', patient_invoice_view, name='patient_invoice'),
    path('patient/delete/<int:pk>/',delete_patient, name='delete_patient'),
    path('medicines/by-place/', medicine_by_place_view, name='medicine_by_place'),
    path('places/medicines/', allplaces_medicine_list_view, name='all_places_medicines'),
    path('patient/<int:patient_id>/invoices/', list_invoices, name='list_invoices'),
    path('patient/<int:patient_id>/invoice/<str:date_str>/', patient_invoice_view_by_date, name='patient_invoice_view_by_date'),
]