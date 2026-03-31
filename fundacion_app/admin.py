from django.contrib import admin
from .models import CategoriaGasto, Gasto, Hogares, MovimientoCaja

@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo_movimiento', 'tipo')
    search_fields = ('nombre',)
    list_filter = ('tipo_movimiento', 'tipo')

@admin.register(Hogares)
class HogaresAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'email')
    search_fields = ('nombre',)

@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'hogar', 'tipo', 'descripcion', 'categoria', 'monto_formateado', 'pagado')
    list_filter = ('hogar', 'tipo', 'pagado', 'categoria', 'fecha')
    search_fields = ('descripcion',)
    ordering = ('-fecha',)
    list_editable = ('pagado',)

    def monto_formateado(self, obj):
        return f"${obj.monto:,.2f}"
    monto_formateado.short_description = 'Monto'

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista principal
    list_display = ('fecha', 'descripcion', 'categoria', 'monto_formateado', 'pagado')
    
    # Filtros laterales (clave para el contador)
    list_filter = ('pagado', 'categoria', 'fecha')
    
    # Buscador por descripción
    search_fields = ('descripcion',)
    
    # Orden por defecto (lo más reciente primero)
    ordering = ('-fecha',)
    
    # Permite editar el estado "pagado" directamente desde la lista sin entrar al detalle
    list_editable = ('pagado',)

    # Formateo de moneda para que se vea más profesional
    def monto_formateado(self, obj):
        return f"${obj.monto:,.2f}"
    monto_formateado.short_description = 'Monto'
