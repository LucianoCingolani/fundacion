from django.contrib import messages
from django.shortcuts import redirect, render
from fundacion_app.forms import DonanteForm

# Create your views here.


def home(request):
    return render(request, 'home.html')

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