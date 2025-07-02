from django.urls import path
from .views import index,login,adminview,pharmacistview,doctorview

urlpatterns = [
    path('', index, name='index'),
    path('login/', login, name='login'),
    path('adminview/', adminview, name='adminview'),
    path('pharmacistview/', pharmacistview, name='pharmacistview'),
    path('doctorview/', doctorview, name='doctorview'),
]