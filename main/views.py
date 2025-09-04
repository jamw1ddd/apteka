from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from main.models import Medicine, CustomUser, MedicineHistory, Patient, PatientMedicine, Place
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta,datetime
from django.db.models import Sum,Count,DecimalField,ExpressionWrapper, IntegerField,F
from django.db.models.functions import TruncMinute
from django.db import transaction

@login_required
def stats_view(request):
    start_str = request.GET.get('start_date')
    end_str = request.GET.get('end_date')
    period = request.GET.get('period') or '30'
    today = datetime.today().date()
    # 🔹 Avval period tekshiriladi, faqat sana kiritilmagan bo‘lsa
    if period in ['7', '1', '30'] and not (start_str and end_str):
        if period == '7':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == '1':
            start_date = end_date = today
        else:  # default 30 kun
            start_date = today - timedelta(days=30)
            end_date = today
    elif start_str and end_str:
        # 🔹 Agar foydalanuvchi sana tanlagan bo‘lsa
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            start_date = today - timedelta(days=30)
            end_date = today
    else:
        # 🔹 Default 30 kun
        start_date = today - timedelta(days=30)
        end_date = today
    # 🔹 Statistikalar
    incoming = Medicine.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).aggregate(total=Sum('quantity'))['total'] or 0
    used = PatientMedicine.objects.filter(
        date__date__range=(start_date, end_date)
    ).annotate(
        total_quantity=ExpressionWrapper(
            F('boxes_given') * F('medicine__box_quantity') + F('units_given'),
            output_field=IntegerField()
        )
    ).aggregate(total=Sum('total_quantity'))['total'] or 0
    transferred = MedicineHistory.objects.filter(
        action='transferred',
        created_at__date__range=(start_date, end_date)
    ).aggregate(total=Sum('quantity'))['total'] or 0
    remaining = Medicine.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0
    new_patients = Patient.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).count()
    history = MedicineHistory.objects.filter(
        created_at__date__range=(start_date, end_date)
    ).select_related('medicine', 'user', 'to_user', 'to_place').order_by('-created_at')
    context = {
        'incoming': incoming,
        'used': used,
        'transferred': transferred,
        'remaining': remaining,
        'new_patients': new_patients,
        'start_date': start_date,
        'end_date': end_date,
        'period': period,
        'history': history
    }
    return render(request, 'admindashboard.html', context)

@login_required
def doctorview(request):
    user = request.user
    if user.role == "doctor":
        # faqat o'z joylari
        places = user.place.all()
    else:
        # admin yoki boshqa rollar hamma joylarni ko'radi
        places = Place.objects.all()
    # Har bir place uchun tegishli dorilarni yig'amiz
    place_medicines = []
    for place in places:
        medicines = Medicine.objects.filter(place=place)
        place_medicines.append({
            'place': place,
            'medicines': medicines
        })
    return render(request, 'doctor.html', {'place_medicines': place_medicines})

@login_required
def add_medicine_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        weight = request.POST.get('weight')
        category = request.POST.get('category')
        price = request.POST.get('price')
        box_quantity = request.POST.get('box_quantity', 1)  # qutidagi dona soni
        quantity = request.POST.get('quantity')  # quti soni
        expiry_date = request.POST.get('expiry_date')
        # Hamma required maydonlar to‘ldirilganini tekshiramiz
        if not all([name, category, price, quantity, box_quantity]):
            return render(request, 'addmedicine.html', {
                "error": "Hamma maydonlar to‘ldirilishi shart!"
            })
        # Ma'lumotlarni to'g'ri formatga o'tkazamiz
        price = Decimal(price)
        quantity = int(quantity)
        box_quantity = int(box_quantity)

        if expiry_date:
            expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        else:
            expiry_date = None
        # Dori yaratamiz
        medicine = Medicine.objects.create(
            name=name,
            weight=weight,
            category=category,
            price=price,
            quantity=quantity,         # omborda nechta quti
            box_quantity=box_quantity, # qutidagi dona soni
            expiry_date=expiry_date,
            owner=request.user,
        )
        # Tarixga yozamiz
        MedicineHistory.objects.create(
            medicine=medicine,
            user=request.user,
            quantity=quantity,
            action='added'
        )
        return redirect('listmedicine')
    return render(request, 'addmedicine.html')

@login_required
def medicine_list_view(request):
    medicines = Medicine.objects.filter(place__isnull=True).order_by('-created_at')
    return render(request, 'listmedicine.html', {'medicines': medicines})

@login_required
def place_medicine_list_view(request, place_id):
    place = get_object_or_404(Place, id=place_id)
    medicines = Medicine.objects.filter(place=place).order_by('-created_at')
    return render(request, 'place_medicine_list.html', {'place': place, 'medicines': medicines})

@login_required
def allplaces_medicine_list_view(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden("Faqat admin foydalanuvchilar kirishi mumkin.")
    # Barcha joylar va har bir joy uchun dorilarni ajratib chiqaramiz
    places = Place.objects.all().prefetch_related('medicine_set')
    return render(request, 'all_place_medicines.html', {
        'places': places
    })

@login_required
def transfer_medicine_view(request):
    places = Place.objects.all()
    user_role = request.user.role
    if user_role not in ['admin', 'staff']:
        messages.error(request, "Sizda dori chiqarishga ruxsat yo'q.")
        return redirect('givemedicine')
    if request.method == 'POST':
        medicine_name = request.POST.get('name', '').strip()
        sale_type = request.POST.get('sale_type')  # 'unit' yoki 'box'
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, "Noto‘g‘ri miqdor kiritildi.")
            return redirect('givemedicine')
        place_id = request.POST.get('place')
        place = get_object_or_404(Place, id=place_id)
        # Ombordagi dori (admin ombor = place is null)
        admin_medicine = Medicine.objects.filter(
            name__iexact=medicine_name,
            place__isnull=True
        ).first()
        if not admin_medicine:
            messages.error(request, f"{medicine_name} nomli dori topilmadi.")
            return redirect('givemedicine')
        # jami dona omborda
        admin_total_units = admin_medicine.total_units
        # qancha dona transfer qilinadi
        if sale_type == 'box':
            transfer_units = quantity * admin_medicine.box_quantity
        elif sale_type == 'unit':
            transfer_units = quantity
        else:
            messages.error(request, "Sotish turini tanlang (unit/box).")
            return redirect('givemedicine')
        if admin_total_units < transfer_units:
            messages.error(request, "Yetarli dori mavjud emas.")
            return redirect('givemedicine')
        # atomik blok — hamma update yoki hech narsa
        with transaction.atomic():
            # --- ombordan ayiramiz ---
            new_admin_total = admin_total_units - transfer_units
            admin_medicine.quantity = new_admin_total // admin_medicine.box_quantity
            admin_medicine.extra_units = new_admin_total % admin_medicine.box_quantity
            admin_medicine.save()
            # --- manzildagi dori yangilanadi yoki yaratiladi ---
            place_medicine = Medicine.objects.filter(
                name__iexact=medicine_name,
                place=place,
                owner=None
            ).first()
            if place_medicine:
                new_place_total = place_medicine.total_units + transfer_units
                place_medicine.quantity = new_place_total // place_medicine.box_quantity
                place_medicine.extra_units = new_place_total % place_medicine.box_quantity
                place_medicine.save()
            else:
                # yangi yozuvda ham quantity va extra_units to'g'ri saqlanadi
                place_qty = transfer_units // admin_medicine.box_quantity
                place_extra = transfer_units % admin_medicine.box_quantity
                place_medicine = Medicine.objects.create(
                    name=medicine_name,
                    category=admin_medicine.category,
                    generic_name=admin_medicine.generic_name,
                    weight=admin_medicine.weight,
                    price=admin_medicine.price,
                    quantity=place_qty,
                    extra_units=place_extra,
                    box_quantity=admin_medicine.box_quantity,
                    expiry_date=admin_medicine.expiry_date,
                    place=place,
                    owner=None,
                )
            if sale_type == "box":
                action_text = "quti ko'chirildi"
            elif sale_type == "unit":
                action_text = "dona ko'chirildi"
            else:
                action_text = "ko'chirildi"
            # Tarixga yozamiz
            MedicineHistory.objects.create(
                medicine=admin_medicine,
                user=request.user,
                to_place=place,
                quantity=transfer_units,   # saqlashni donalarda ham qilsak ma'qul
                action=action_text
            )
        return redirect('listmedicine')
    return render(request, 'givemedicine.html', {
        'places': places,
        'medicines': Medicine.objects.filter(place__isnull=True)
    })

@login_required
def medicine_history_view(request):
    history = MedicineHistory.objects.select_related('medicine', 'user', 'to_user').order_by('-created_at')
    return render(request, 'medicine_history.html', {'history': history})

User = get_user_model()

@login_required
def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        place_id = request.POST.get('place')  # Bu ID bo'lishi kerak
        who = request.POST.get('who')
        # Avval foydalanuvchi yaratamiz
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.role = role
        user.who = who
        user.save()
        # ManyToManyField bo'lsa .set() ishlatamiz
        if place_id:
            place_obj = Place.objects.get(id=place_id)
            user.place.set([place_obj])  # ✅ ManyToManyField uchun to‘g‘ri usul
        return redirect('employee_list')
    return render(request, 'addstaff.html', {'places': Place.objects.all()})

@login_required
def employee_list(request):
    user = request.user
    if user.role == 'admin':
        users = CustomUser.objects.all().exclude(id=user.id).exclude(username__in=['admin', 'jamw1ddd'])  # Admin o‘zini ko‘rmaydi
    else:
        users = CustomUser.objects.filter(id=user.id)  # Faqat o‘zini ko‘radi
    return render(request, 'listemployee.html', {'users': users})

@login_required
def employeeview(request):
    user = request.user
    if user.role == "staff":
        places = user.place.all()  # Foydalanuvchiga biriktirilgan barcha joylar
    else:
        places = Place.objects.all()  # Adminlar uchun barcha joylar
    # Har bir place uchun tegishli dorilarni yig'amiz
    place_medicines = []
    for place in places:
        medicines = Medicine.objects.filter(place=place)
        place_medicines.append({
            'place': place,
            'medicines': medicines
        })
    return render(request, 'employee.html', {'place_medicines': place_medicines})

@login_required
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
        return redirect('list_patients')  
    return render(request, 'addpatient.html')

@login_required
def list_patients(request):
    patients = Patient.objects.all()
    return render(request, 'listpatient.html', {'patients': patients})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('dashboard_stats')  # admin sahifa
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

@login_required
def give_medicine_to_patient_view(request):
    if request.user.role != 'doctor':
        messages.error(request, "Sizda dori yozishga ruxsat yo'q.")
        return redirect('home')
    user_places = request.user.place.all()
    selected_place = user_places.first()
    patients = Patient.objects.all()
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        medicine_ids = request.POST.getlist('medicines')
        quantities = request.POST.getlist('quantities')
        patient = get_object_or_404(Patient, id=patient_id)
        now_time = timezone.localtime(timezone.now())
        for i, med_id in enumerate(medicine_ids):
            quantity = int(quantities[i])  # jami so‘ralgan dona
            medicine = get_object_or_404(Medicine, id=med_id, place=selected_place)
            # Yetarli umumiy dona borligini tekshirish
            if medicine.total_units < quantity:
                messages.error(request, f"{medicine.name} uchun yetarli miqdor mavjud emas.")
                continue
            # Quti va dona bo‘yicha hisoblash
            boxes_to_deduct, remainder_units = divmod(quantity, medicine.box_quantity)
            # Agar qutidan yechib bo‘lsa
            if boxes_to_deduct > medicine.quantity:
                boxes_to_deduct = medicine.quantity
                remainder_units = quantity - boxes_to_deduct * medicine.box_quantity
            # ➤ Bemor uchun yozib qo‘yish
            PatientMedicine.objects.create(
                patient=patient,
                medicine=medicine,
                boxes_given=boxes_to_deduct,
                units_given=remainder_units,
                prescribed_by=request.user,
                date=now_time
            )
            # ➤ Omborni yangilash
            medicine.quantity -= boxes_to_deduct
            if remainder_units > 0:
                if remainder_units <= medicine.extra_units:
                    # faqat qoldiq donalardan kamaytirish
                    medicine.extra_units -= remainder_units
                else:
                    # qoldiq yetmasa -> 1 quti ochib, qoldiqni yangilash
                    if medicine.quantity > 0:
                        medicine.quantity -= 1
                        needed_from_new_box = remainder_units - medicine.extra_units
                        medicine.extra_units = medicine.box_quantity - needed_from_new_box
                    else:
                        messages.error(request, f"{medicine.name} uchun yetarli dona mavjud emas.")
                        continue
            medicine.save()
            # ➤ Tarixga yozish
            MedicineHistory.objects.create(
                medicine=medicine,
                user=request.user,
                to_patient=patient,
                quantity=quantity,
                action='Bemorga chiqarildi',
            )
        return redirect(
            'patient_invoice_view_by_date',
            patient_id=patient.id,
            date_str=now_time.strftime("%Y-%m-%d_%H-%M")
        )
    medicines = Medicine.objects.filter(place=selected_place)
    return render(request, 'give_medicine_to_patient.html', {
        'patients': patients,
        'medicines': medicines
    })

@login_required
def patient_invoice_view(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    prescriptions = PatientMedicine.objects.filter(patient=patient)
    # jami narx
    subtotal = sum(p.total_price for p in prescriptions)
    processing_fee = Decimal("10.00")
    tax = subtotal * Decimal("0.10")
    total = subtotal #+ processing_fee + tax
    first_prescription = prescriptions.first()
    prescribed_by = first_prescription.prescribed_by if first_prescription else None
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'created_at': timezone.now(),
        'invoice_number': f"INV{patient.id:06d}",
        'subtotal': f"{subtotal:.2f}",
        'processing_fee': f"{processing_fee:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}",
        'prescribed_by': prescribed_by,
    }
    return render(request, 'patient_detail.html', context)

@login_required
def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    patient.delete()
    return redirect('list_patients') 

@login_required
def medicine_by_place_view(request):
    places = Place.objects.all()
    data = []
    for place in places:
        # Ushbu joyga biriktirilgan foydalanuvchilar (rahbarlar)
        leaders = CustomUser.objects.filter(place=place)
        # Ushbu joy uchun dorilarni topamiz
        medicines = Medicine.objects.filter(owner__place=place)
        data.append({
            'place': place,
            'leaders': leaders,
            'medicines': medicines,
        })
    return render(request, 'medicine_by_place.html', {'data': data})

@login_required
def list_invoices(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    invoices = (
        PatientMedicine.objects
        .filter(patient=patient)
        .annotate(chek_sana=TruncMinute('date'))
        .values('chek_sana')
        .annotate(
            total=Sum(
                ExpressionWrapper(
                    # Umumiy narx: (quti * qutidagi dona + dona) * (quti narxi / qutidagi dona)
                    (F('boxes_given') * F('medicine__box_quantity') + F('units_given'))
                    * (F('medicine__price') / F('medicine__box_quantity')),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
            items_count=Count('id')
        )
        .order_by('-chek_sana')
    )
    # datetime → string formatlash
    for inv in invoices:
        inv['date_str'] = inv['chek_sana'].strftime('%Y-%m-%d_%H-%M')
    return render(request, 'invoice_list.html', {
        'patient': patient,
        'invoices': invoices
    })

@login_required
def patient_invoice_view_by_date(request, patient_id, date_str):
    patient = get_object_or_404(Patient, id=patient_id)
    invoice_datetime = datetime.strptime(date_str, "%Y-%m-%d_%H-%M")
    start_time = invoice_datetime
    end_time = invoice_datetime + timedelta(minutes=1)
    prescriptions = PatientMedicine.objects.filter(
        patient=patient,
        date__gte=start_time,
        date__lt=end_time
    )
    subtotal = sum(p.total_price for p in prescriptions)
    processing_fee = Decimal("10.00")
    tax = subtotal * Decimal("0.10")
    total = subtotal
    first_prescription = prescriptions.first()
    prescribed_by = first_prescription.prescribed_by if first_prescription else None
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'created_at': invoice_datetime,
        'invoice_number': f"INV{patient.id:06d}",
        'subtotal': f"{subtotal:.2f}",
        'processing_fee': f"{processing_fee:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}",
        'prescribed_by': prescribed_by,
    }
    return render(request, 'patient_detail.html', context)

@login_required
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    # Agar foydalanuvchi admin bo'lmasa, ruxsatni cheklaymiz
    if request.user.role not in ['admin', 'staff','doctor']:
        messages.error(request, "Sizda dorini o‘zgartirish huquqi yo‘q.")
        return redirect('listmedicine')
    if request.method == 'POST':
        medicine.name = request.POST.get('name', medicine.name)
        medicine.generic_name = request.POST.get('generic_name', medicine.generic_name)
        medicine.weight = request.POST.get('weight', medicine.weight)
        medicine.category = request.POST.get('category', medicine.category)
        # Narx, box_quantity va quantity integer/decimal sifatida saqlaymiz
        try:
            medicine.price = float(request.POST.get('price', medicine.price))
        except (ValueError, TypeError):
            medicine.price = medicine.price
        try:
            medicine.box_quantity = int(request.POST.get('box_quantity', medicine.box_quantity))
        except (ValueError, TypeError):
            medicine.box_quantity = medicine.box_quantity
        try:
            medicine.quantity = int(request.POST.get('quantity', medicine.quantity))
        except (ValueError, TypeError):
            medicine.quantity = medicine.quantity
        expiry_date = request.POST.get('expiry_date')
        medicine.expiry_date = expiry_date if expiry_date else None
        medicine.save()
        messages.success(request, f"{medicine.name} muvaffaqiyatli yangilandi.")
        return redirect('listmedicine')
    return render(request, 'medicine_edit.html', {
        'medicine': medicine,
        'categories': Medicine.CATEGORY_CHOICES
    })