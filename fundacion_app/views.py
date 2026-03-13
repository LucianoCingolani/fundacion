from datetime import datetime
import smtplib
from django.contrib import messages
from django.shortcuts import redirect, render
from fundacion_app.forms import DonacionForm, DonanteForm
from django.db.models import Sum
from fundacion_app.models import Donacion, Donante
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mass_mail

# Create your views here.

@login_required
def home(request):
    # 1. Contar total de donantes
    total_donantes = Donante.objects.count()

    # 2. Calcular recaudación del mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    recaudacion_mes = Donacion.objects.filter(
        fecha_pago__month=mes_actual,
        fecha_pago__year=anio_actual
    ).aggregate(Sum('monto'))['monto__sum'] or 0

    # 3. Obtener las últimas 5 donaciones para la tabla
    ultimas_donaciones = Donacion.objects.select_related('donante').order_by('-fecha_pago')[:5]

    context = {
        'total_donantes': total_donantes,
        'recaudacion_mes': recaudacion_mes,
        'ultimas_donaciones': ultimas_donaciones,
    }
    
    return render(request, 'home.html', context)

@login_required
def registrar_donante(request):
    if request.method == 'POST':
        form = DonanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Donante registrado con éxito!') # Mensaje de éxito
            return redirect('home')
    else:
        form = DonanteForm()
    
    return render(request, 'donante_form.html', {'form': form})

@login_required
def lista_donantes(request):
    donantes = Donante.objects.all().order_by('-fecha_alta') # Los más nuevos primero
    return render(request, 'donantes_list.html', {'donantes': donantes})

@login_required
def registrar_donacion(request):
    if request.method == 'POST':
        form = DonacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Donación registrada correctamente!')
            return redirect('lista_donantes')
    else:
        form = DonacionForm()
    return render(request, 'donacion_form.html', {'form': form})

@login_required
def enviar_mail_masivo(request):
    if request.method == 'POST':
        try:
            # Prueba básica: mandátelo a vos mismo primero
            send_mail(
                subject='Prueba de Conexión Fundación',
                message='Si recibís esto, la configuración de Gmail es correcta.',
                from_email=None, # Usa el EMAIL_HOST_USER por defecto
                recipient_list=['tu-email@gmail.com'], # Poné tu mail real acá
                fail_silently=False,
            )
            messages.success(request, "¡Mail de prueba enviado con éxito!")
        except smtplib.SMTPAuthenticationError:
            messages.error(request, "Error de autenticación: Revisá la App Password.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error: {e}")
            
        return redirect('home')
    
    return render(request, 'enviar_mail.html')