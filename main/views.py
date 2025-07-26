from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from main.models import Medicine, CustomUser, MedicineHistory, Patient
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model

def adminview(request):
    return render(request, 'adminn.html')

@login_required
def doctorview(request):
    user = request.user

    if user.role == "doctor":
        # Faqat o'zining `place` ga tegishli hodimlar chiqsin (o'zini chiqarib tashlaymiz)
        staff_members = CustomUser.objects.filter(place=user.place).exclude(id=user.id)
    else:
        # Admin yoki boshqa rollar uchun barcha hodimlar chiqadi
        staff_members = CustomUser.objects.all()

    return render(request, 'doctor.html', {'staff_members': staff_members})

@login_required
def add_medicine_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        generic_name = request.POST.get('generic_name')
        weight = request.POST.get('weight')
        category = request.POST.get('category')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        expiry_date = request.POST.get('expiry_date')
        # Hamma required maydonlar to‘ldirilganini tekshiramiz
        if not all([name, generic_name, category, price, quantity]):
            messages.error(request, "Iltimos, kerakli maydonlarni to‘ldiring.")
            return render(request, 'addmedicine.html')

        medicine = Medicine.objects.create(
            name=name,
            generic_name=generic_name,
            weight=weight,
            category=category,
            price=price,
            quantity=quantity,
            expiry_date=expiry_date or None,
            owner=request.user,
        )

        # Tarixga yozish        
        MedicineHistory.objects.create(
            medicine=medicine,
            user=request.user,
            quantity=quantity,
            action='added'
        )

        messages.success(request, "Dori muvaffaqiyatli qo‘shildi.")
        return redirect('listmedicine')  # Bu sizdagi dori ro‘yxati sahifasi nomi bo‘lishi kerak

    return render(request, 'addmedicine.html')

@login_required
def medicine_list_view(request):
    medicines = Medicine.objects.filter(owner=request.user).order_by('-created_at')
    return render(request, 'listmedicine.html', {'medicines': medicines})

@login_required
def transfer_medicine_view(request):
    user_role = request.user.role

    # Ruxsat faqat admin va staffga
    if user_role not in ['admin', 'staff']:
        messages.error(request, "Sizda dori chiqarishga ruxsat yo'q.")
        return redirect('givemedicine')
    # Admin -> faqat staff foydalanuvchilar
    # Staff -> faqat doctor foydalanuvchilar
    if user_role == 'admin':
        users = CustomUser.objects.filter(role='staff')
    elif user_role == 'staff':
        users = CustomUser.objects.filter(role='doctor')

    if request.method == 'POST':
        medicine_name = request.POST.get('name', '').strip()
        category = request.POST.get('category')
        quantity = int(request.POST.get('quantity'))
        price = float(request.POST.get('price'))
        employee_id = request.POST.get('employee')

        print("Sizning rolingiz:", request.user.role)
        print("Yuborilgan employee_id:", employee_id)

        admin_medicine = Medicine.objects.filter(
            name=medicine_name,
            category=category,
            owner=request.user
        ).first()

        if not admin_medicine:
            messages.error(request, "Bunday dori topilmadi.")
            return redirect('givemedicine')

        if admin_medicine.quantity < quantity:
            messages.error(request, "Yetarli dori mavjud emas.")
            return redirect('givemedicine')

        employee = get_object_or_404(CustomUser, id=employee_id)

        print("Tanlangan foydalanuvchi:", employee.username)
        print("Uning roli:", employee.role)

        # Rol tekshiruvi: admin -> staff, staff -> doctor
        if (user_role == 'admin' and employee.role != 'staff') or (user_role == 'staff' and employee.role != 'doctor'):
            messages.error(request, "Siz faqat mos foydalanuvchilarga dori bera olasiz.")
            return redirect('givemedicine')

        employee_medicine, created = Medicine.objects.get_or_create(
            name=medicine_name,
            category=category,
            owner=employee,
            defaults={
                'generic_name': admin_medicine.generic_name,
                'weight': admin_medicine.weight,
                'price': price,
                'quantity': 0,
                'expiry_date': admin_medicine.expiry_date,
            }
        )
        employee_medicine.quantity += quantity
        employee_medicine.save()

        admin_medicine.quantity -= quantity
        admin_medicine.save()

        MedicineHistory.objects.create(
            medicine=admin_medicine,
            user=request.user,
            to_user=employee,
            quantity=quantity,
            action='transferred'
        )

        messages.success(request, f"{employee.username} foydalanuvchisiga {quantity} ta {medicine_name} chiqarildi.")
        return redirect('listmedicine')

    return render(request, 'givemedicine.html', {'users': users})


@login_required
def medicine_history_view(request):
    history = MedicineHistory.objects.select_related('medicine', 'user', 'to_user').order_by('-created_at')
    return render(request, 'medicine_history.html', {'history': history})

User = get_user_model()

def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        place = request.POST.get('place')
        who = request.POST.get('who')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.role = role
        user.place = place
        user.who = who
        user.save()

        return redirect('employee_list')  # yoki boshqa sahifaga
    return render(request, 'addstaff.html')


@login_required
def employee_list(request):
    user = request.user
    if user.role == 'admin':
        users = CustomUser.objects.all().exclude(id=user.id)  # Admin o'zini ko'rmaydi
    else:
        users = CustomUser.objects.filter(id=user.id)  # Faqat o'zini ko'radi

    return render(request, 'listemployee.html', {'users': users})

@login_required
def employeeview(request):
    user = request.user
    # Agar foydalanuvchi katta hamshira bo‘lsa:
    if user.role == "staff" and user.who == "Bosh hamshira":
        # O‘sha etajdagi boshqa hodimlar chiqsin (o‘zini o‘zi chiqarib yuboramiz)
        staff_members = CustomUser.objects.filter(place=user.place).exclude(id=user.id)
    else:
        # Aks holda barcha hodimlar chiqadi (adminlar uchun yoki boshqa rollar)
        staff_members = CustomUser.objects.all()

    return render(request, 'employee.html', {'staff_members': staff_members})

def add_patient(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        # Create new patient
        Patient.objects.create(
            name=name,
            surname=surname,
            phone=phone,
            address=address
        )
        #return redirect('list_patients')  
    return render(request, 'addpatient.html')

def list_patients(request):
    patients = Patient.objects.all()
    return render(request, 'listpatient.html', {'patients': patients})

@login_required
def user_medicines_view(request, user_id):
    staff_user = get_object_or_404(CustomUser, id=user_id)
    medicines = Medicine.objects.filter(owner=staff_user)
    return render(request, 'user_medicines.html', {'medicines': medicines, 'staff_user': staff_user})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            if user.role == 'admin':
                return redirect('adminview')  # admin sahifa
            elif user.role == 'staff':
                return redirect('employee')  # staff sahifa
            elif user.role == 'doctor':
                return redirect('doctor')  # doctor sahifa
            else:
                return redirect('login')  # fallback sahifa
        else:
            messages.error(request, "Login yoki parol noto‘g‘ri!")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
