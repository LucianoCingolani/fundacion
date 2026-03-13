from django.contrib import messages
from django.shortcuts import redirect, render
from fundacion_app.forms import DonacionForm, DonanteForm
from fundacion_app.models import Donante
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def home(request):
    return render(request, 'home.html')

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