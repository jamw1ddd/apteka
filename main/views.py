from django.shortcuts import render

# Create your views here.
def index(request):
    """
    Render the index page.
    """
    return render(request, 'index.html')   

def login(request):
    """
    Render the login page.
    """
    return render(request, 'login.html')

def adminview(request):
    """
    Render the admin page.
    """
    return render(request, 'admin.html')

def pharmacistview(request):
    """
    Render the pharmacist page.
    """
    return render(request, 'pharmacist.html')

def doctorview(request):
    """
    Render the doctor page.
    """
    return render(request, 'doctor.html')