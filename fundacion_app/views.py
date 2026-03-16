from datetime import datetime
import json
import smtplib
import traceback
from django.contrib import messages
from django.shortcuts import redirect, render
from fundacion_app.forms import DonacionForm, DonanteForm
from django.db.models import Sum
from fundacion_app.models import CategoriaGasto, Donacion, Donante, Gasto
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail

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
            tipo = request.POST.get('tipo_donante')
            asunto = request.POST.get('asunto')
            mensaje_base = request.POST.get('mensaje')
            
            donantes = Donante.objects.filter(tipo_donante=tipo)
            
            for donante in donantes:
                if donante.mail: 
                    send_mail(
                        asunto, 
                        f"Hola {donante.nombre}\n\n{mensaje_base}", 
                        None, 
                        [donante.mail]
                    )
            
            messages.success(request, "Correos enviados con éxito.")
            return redirect('home')
            
        except Exception as e:
            print(f"ERROR DETECTADO: {e}")
            messages.error(request, f"Hubo un error al enviar: {e}")
            return redirect('home') # Es mejor redirigir con el mensaje de error que dejar la pantalla amarilla

    return render(request, 'enviar_mail.html')

def dashboard_cashflow(request):
    mes_actual = datetime.now().month
    total_gastos = Gasto.objects.filter(fecha__month=mes_actual).aggregate(Sum('monto'))['monto__sum'] or 0
    gastos_por_categoria = Gasto.objects.filter(fecha__month=mes_actual).values('categoria__nombre').annotate(total=Sum('monto'))
    categorias = CategoriaGasto.objects.all()
    pendientes_pago = Gasto.objects.filter(fecha__month=mes_actual, pagado=False).aggregate(Sum('monto'))['monto__sum'] or 0
    gastos_query = Gasto.objects.values('categoria__nombre').annotate(total=Sum('monto'))

    labels = [item['categoria__nombre'] for item in gastos_query]
    values = [float(item['total']) for item in gastos_query]

    context = {
        'total_gastos': total_gastos,
        'gastos_por_categoria': gastos_por_categoria,
        'ultimos_gastos': Gasto.objects.all().order_by('-fecha')[:10],
        'categorias': categorias,
        'pendientes_pago': pendientes_pago,
        'chart_labels': json.dumps(labels),
        'chart_values': json.dumps(values),
    }
    return render(request, 'gastos.html', context)

def crear_gasto(request):
    if request.method == 'POST':
        try:
            descripcion = request.POST.get('descripcion')
            categoria_id = request.POST.get('categoria')
            monto = request.POST.get('monto')
            fecha = request.POST.get('fecha')
            pagado = request.POST.get('pagado') == 'on' # Checkbox logic

            categoria = CategoriaGasto.objects.get(id=categoria_id)

            Gasto.objects.create(
                descripcion=descripcion,
                categoria=categoria,
                monto=monto,
                fecha=fecha,
                pagado=pagado
            )
            messages.success(request, "Gasto registrado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al registrar: {e}")
            
    return redirect('dashboard_cashflow') # Nombre de tu url de cashflow