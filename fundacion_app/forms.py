from django import forms
from .models import Donante

class DonanteForm(forms.ModelForm):
    class Meta:
        model = Donante
        fields = '__all__'
        widgets = {
            field: forms.TextInput(attrs={'class': 'w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none'})
            for field in ['seguido_por', 'referente', 'segmentacion', 'nombre', 'apellido', 'empresa', 'cargo', 'celular']
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalización de campos específicos
        self.fields['mail'].widget = forms.EmailInput(attrs={'class': 'w-full p-2 border border-slate-300 rounded-lg'})
        self.fields['monto_mensual'].widget = forms.NumberInput(attrs={'class': 'w-full p-2 border border-slate-300 rounded-lg'})
        self.fields['fecha_alta'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border border-slate-300 rounded-lg'})
        self.fields['fecha_baja'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border border-slate-300 rounded-lg'})
        
        # Estilo para los Selects
        select_class = "w-full p-2 border border-slate-300 rounded-lg bg-white"
        self.fields['origen'].widget.attrs.update({'class': select_class})
        self.fields['trato'].widget.attrs.update({'class': select_class})
        self.fields['genero'].widget.attrs.update({'class': select_class})
        self.fields['tipo_donante'].widget.attrs.update({'class': select_class})