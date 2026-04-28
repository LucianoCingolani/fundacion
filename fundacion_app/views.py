from datetime import datetime
from decimal import Decimal
import json
import smtplib
import traceback
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from fundacion_app.forms import DonacionForm, DonanteForm
from django.db.models import Q, Sum
from fundacion_app.models import CategoriaGasto, Donacion, Donante, Gasto, Hogares, MovimientoCaja
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Create your views here.


CHART_COLORS = [
    '#16a34a', '#dc2626', '#f97316', '#eab308', '#0891b2',
    '#2563eb', '#7c3aed', '#db2777', '#0f766e', '#ea580c',
]


def _parse_int_query_param(value, default):
    if value is None:
        return default

    normalized = str(value).replace('\xa0', '').replace(' ', '').strip()
    if not normalized:
        return default

    try:
        return int(normalized)
    except (TypeError, ValueError):
        return default


def _format_currency(value):
    return f"${value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _build_categoria_chart_data(movimientos_qs, tipo):
    categorias_qs = (
        movimientos_qs
        .filter(tipo=tipo)
        .values('categoria__nombre')
        .annotate(total=Sum('monto'))
        .order_by('-total')
    )

    labels = []
    data = []
    detail_rows = []
    total_general = Decimal('0.00')

    for index, item in enumerate(categorias_qs):
        nombre_categoria = item['categoria__nombre'] or 'Sin categoría'
        total = item['total'] or Decimal('0.00')
        color = CHART_COLORS[index % len(CHART_COLORS)]
        labels.append(nombre_categoria)
        data.append(float(total))
        detail_rows.append({
            'categoria': nombre_categoria,
            'total': total,
            'color': color,
        })
        total_general += total

    for row in detail_rows:
        row['porcentaje'] = (row['total'] / total_general * 100) if total_general else Decimal('0.00')

    return {
        'labels': labels,
        'data': data,
        'detail_rows': detail_rows,
        'total': total_general,
    }


def _build_cashflow_report_pdf(response, hogar_activo, mes, anio, total_ingresos, total_egresos, balance, ingresos_chart, egresos_chart, movimientos_qs):
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='ReportTitle', parent=styles['Title'], fontSize=20, leading=24, textColor=colors.HexColor('#0f172a')))
    styles.add(ParagraphStyle(name='ReportSubtitle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#64748b')))
    styles.add(ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#1e293b')))
    styles.add(ParagraphStyle(name='SmallCenter', parent=styles['Normal'], fontSize=8, leading=10, alignment=TA_CENTER, textColor=colors.HexColor('#475569')))

    story = []

    story.append(Paragraph('Reporte de Flujo de Caja', styles['ReportTitle']))
    story.append(Paragraph(f'Hogar: {hogar_activo.nombre} | Período: {mes:02d}/{anio}', styles['ReportSubtitle']))
    story.append(Spacer(1, 8))
    story.append(Spacer(1, 12))

    resumen_data = [
        ['Indicador', 'Monto'],
        ['Total ingresos', _format_currency(total_ingresos)],
        ['Total egresos', _format_currency(total_egresos)],
        ['Balance', _format_currency(balance)],
    ]
    resumen_table = Table(resumen_data, colWidths=[90 * mm, 50 * mm])
    resumen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 16))

    def add_chart_section(title, chart_data, accent_color):
        story.append(Paragraph(title, styles['SectionTitle']))
        story.append(Spacer(1, 6))

        if not chart_data['data']:
            story.append(Paragraph('No hay datos para este gráfico en el período seleccionado.', styles['BodyText']))
            story.append(Spacer(1, 12))
            return

        drawing = Drawing(170 * mm, 80 * mm)
        drawing.add(String(85 * mm, 75 * mm, title, textAnchor='middle', fontSize=11, fillColor=colors.HexColor('#334155')))

        pie = Pie()
        pie.x = 20 * mm
        pie.y = 10 * mm
        pie.width = 60 * mm
        pie.height = 60 * mm
        pie.data = chart_data['data']
        pie.labels = []
        pie.sideLabels = True
        pie.simpleLabels = False
        pie.slices.strokeWidth = 0.5
        pie.slices.strokeColor = colors.white
        for index, row in enumerate(chart_data['detail_rows']):
            pie.slices[index].fillColor = colors.HexColor(row['color'])
        drawing.add(pie)
        story.append(drawing)
        story.append(Spacer(1, 6))

        detail_data = [['Color', 'Categoría', 'Monto', '% del total']]
        for row in chart_data['detail_rows']:
            detail_data.append([
                '',
                row['categoria'],
                _format_currency(row['total']),
                f"{row['porcentaje']:.1f}%",
            ])

        detail_table = Table(detail_data, colWidths=[14 * mm, 71 * mm, 38 * mm, 27 * mm])
        detail_table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(accent_color)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ])
        for row_index, row in enumerate(chart_data['detail_rows'], start=1):
            detail_table_style.add('BACKGROUND', (0, row_index), (0, row_index), colors.HexColor(row['color']))
            detail_table_style.add('TEXTCOLOR', (0, row_index), (0, row_index), colors.HexColor(row['color']))
        detail_table.setStyle(detail_table_style)
        story.append(detail_table)
        story.append(Spacer(1, 12))

    add_chart_section('Ingresos por categoría', ingresos_chart, '#15803d')
    story.append(PageBreak())
    add_chart_section('Egresos por categoría', egresos_chart, '#b91c1c')
    story.append(PageBreak())

    story.append(Paragraph('Detalle de movimientos', styles['SectionTitle']))
    story.append(Spacer(1, 6))

    movimientos_data = [['Fecha', 'Tipo', 'Categoría', 'Descripción', 'Monto', 'Estado']]
    for movimiento in movimientos_qs.order_by('fecha', 'id'):
        movimientos_data.append([
            movimiento.fecha.strftime('%d/%m/%Y'),
            movimiento.get_tipo_display(),
            movimiento.categoria.nombre if movimiento.categoria else 'Sin categoría',
            movimiento.descripcion,
            _format_currency(movimiento.monto),
            'Pagado' if movimiento.pagado else 'Pendiente',
        ])

    if len(movimientos_data) == 1:
        movimientos_data.append(['-', '-', '-', 'Sin movimientos en este período', '-', '-'])

    movimientos_table = Table(movimientos_data, colWidths=[22 * mm, 22 * mm, 34 * mm, 55 * mm, 24 * mm, 23 * mm], repeatRows=1)
    movimientos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('ALIGN', (4, 1), (5, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEADING', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(movimientos_table)

    doc.build(story)

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

    mes = _parse_int_query_param(request.GET.get('mes'), datetime.now().month)
    anio = _parse_int_query_param(request.GET.get('anio'), datetime.now().year)

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

    ingresos_chart = _build_categoria_chart_data(movimientos_qs, 'ingreso')
    egresos_chart = _build_categoria_chart_data(movimientos_qs, 'egreso')

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
        'egresos_chart_labels': egresos_chart['labels'],
        'egresos_chart_data': egresos_chart['data'],
        'ingresos_chart_labels': ingresos_chart['labels'],
        'ingresos_chart_data': ingresos_chart['data'],
    }
    return render(request, 'cashflow.html', context)


@login_required
def exportar_cashflow_pdf(request, hogar_id=None):
    hogares = Hogares.objects.order_by('nombre')
    if not hogares.exists():
        messages.error(request, 'No hay hogares configurados para exportar.')
        return redirect('dashboard_cashflow')

    if hogar_id:
        hogar_activo = get_object_or_404(Hogares, pk=hogar_id)
    else:
        hogar_activo = hogares.first()

    mes = _parse_int_query_param(request.GET.get('mes'), datetime.now().month)
    anio = _parse_int_query_param(request.GET.get('anio'), datetime.now().year)

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

    ingresos_chart = _build_categoria_chart_data(movimientos_qs, 'ingreso')
    egresos_chart = _build_categoria_chart_data(movimientos_qs, 'egreso')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cashflow_{hogar_activo.nombre}_{anio}_{mes:02d}.pdf"'
    _build_cashflow_report_pdf(
        response=response,
        hogar_activo=hogar_activo,
        mes=mes,
        anio=anio,
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        balance=balance,
        ingresos_chart=ingresos_chart,
        egresos_chart=egresos_chart,
        movimientos_qs=movimientos_qs,
    )
    return response


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