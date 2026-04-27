from datetime import datetime
from decimal import Decimal
import json
import smtplib
import traceback
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from fundacion_app.forms import DonacionForm, DonanteForm
from django.db.models import Q, Sum
from fundacion_app.models import CategoriaGasto, Donacion, Donante, Gasto, Hogares, MovimientoCaja
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

@login_required
def dashboard_cashflow(request, hogar_id=None):
    hogares = Hogares.objects.order_by('nombre')

    if not hogares.exists():
        return render(request, 'cashflow.html', {'hogares': [], 'hogar_activo': None})

    if hogar_id:
        hogar_activo = get_object_or_404(Hogares, pk=hogar_id)
    else:
        hogar_activo = hogares.first()

    mes = int(request.GET.get('mes', datetime.now().month))
    anio = int(request.GET.get('anio', datetime.now().year))

    movimientos_qs = MovimientoCaja.objects.filter(
        hogar=hogar_activo,
        fecha__month=mes,
        fecha__year=anio,
    ).select_related('categoria').order_by('-fecha')

    totals = movimientos_qs.aggregate(
        total_ingresos=Sum('monto', filter=Q(tipo='ingreso')),
        total_egresos=Sum('monto', filter=Q(tipo='egreso')),
    )
    total_ingresos = totals['total_ingresos'] or Decimal('0.00')
    total_egresos = totals['total_egresos'] or Decimal('0.00')
    balance = total_ingresos - total_egresos

    categorias_ingreso = CategoriaGasto.objects.filter(tipo_movimiento='ingreso').order_by('nombre')
    categorias_egreso = CategoriaGasto.objects.filter(tipo_movimiento='egreso').order_by('nombre')

    egresos_por_categoria_qs = (
        movimientos_qs
        .filter(tipo='egreso')
        .values('categoria__nombre')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    ingresos_por_categoria_qs = (
        movimientos_qs
        .filter(tipo='ingreso')
        .values('categoria__nombre')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    egresos_chart_labels = []
    egresos_chart_data = []
    for item in egresos_por_categoria_qs:
        nombre_categoria = item['categoria__nombre'] or 'Sin categoría'
        egresos_chart_labels.append(nombre_categoria)
        egresos_chart_data.append(float(item['total'] or 0))

    ingresos_chart_labels = []
    ingresos_chart_data = []
    for item in ingresos_por_categoria_qs:
        nombre_categoria = item['categoria__nombre'] or 'Sin categoría'
        ingresos_chart_labels.append(nombre_categoria)
        ingresos_chart_data.append(float(item['total'] or 0))

    context = {
        'hogares': hogares,
        'hogar_activo': hogar_activo,
        'movimientos': movimientos_qs,
        'total_ingresos': total_ingresos,
        'total_egresos': total_egresos,
        'balance': balance,
        'categorias_ingreso': categorias_ingreso,
        'categorias_egreso': categorias_egreso,
        'mes': mes,
        'anio': anio,
        'egresos_chart_labels': egresos_chart_labels,
        'egresos_chart_data': egresos_chart_data,
        'ingresos_chart_labels': ingresos_chart_labels,
        'ingresos_chart_data': ingresos_chart_data,
    }
    return render(request, 'cashflow.html', context)


@login_required
def crear_movimiento(request):
    if request.method == 'POST':
        hogar_id = request.POST.get('hogar')
        try:
            tipo = request.POST.get('tipo')
            descripcion = request.POST.get('descripcion')
            monto = request.POST.get('monto')
            fecha = request.POST.get('fecha')
            pagado = request.POST.get('pagado') == 'on'
            metodo_pago = request.POST.get('metodo_pago', 'Transferencia')
            notas = request.POST.get('notas', '')
            categoria_id = request.POST.get('categoria') or None

            hogar = get_object_or_404(Hogares, pk=hogar_id)
            categoria = CategoriaGasto.objects.get(pk=categoria_id) if categoria_id else None

            MovimientoCaja.objects.create(
                hogar=hogar,
                tipo=tipo,
                descripcion=descripcion,
                monto=monto,
                fecha=fecha,
                pagado=pagado,
                metodo_pago=metodo_pago,
                notas=notas,
                categoria=categoria,
            )
            messages.success(request, 'Movimiento registrado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al registrar: {e}')

    if hogar_id:
        return redirect('dashboard_cashflow_hogar', hogar_id=hogar_id)
    return redirect('dashboard_cashflow')


@login_required
def eliminar_movimiento(request, pk):
    movimiento = get_object_or_404(MovimientoCaja, pk=pk)
    hogar_id = movimiento.hogar_id
    if request.method == 'POST':
        movimiento.delete()
        messages.success(request, 'Movimiento eliminado.')
    return redirect('dashboard_cashflow_hogar', hogar_id=hogar_id)