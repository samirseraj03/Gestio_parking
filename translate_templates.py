import os
import glob
import re

template_dir = 'parking/templates/parking'
files = glob.glob(os.path.join(template_dir, '*.html'))

translations = {
    "Terminal A - Main": '{% trans "Terminal A - Principal" %}',
    "Dashboard Overview": '{% trans "Visión General del Dashboard" %}',
    "Real-time metrics for": '{% trans "Métricas en tiempo real para" %}',
    "Live Occupancy": '{% trans "Ocupación Actual" %}',
    "Daily Revenue": '{% trans "Ingresos Diarios" %}',
    "vs. previous day": '{% trans "vs. día anterior" %}',
    "Active Alerts": '{% trans "Alertas Activas" %}',
    "Requires attention": '{% trans "Requiere atención" %}',
    "Recent Activity": '{% trans "Actividad Reciente" %}',
    ">Time<": '>{% trans "Hora" %}<',
    ">Plate<": '>{% trans "Matrícula" %}<',
    ">Event<": '>{% trans "Evento" %}<',
    "No recent activity.": '{% trans "No hay actividad reciente." %}',
    "Search plates, zones...": '{% trans "Buscar matrículas, zonas..." %}',
    "Terminal A - Principal": "Terminal A - Main", # oops, revert if matched
    
    # Check in
    "Register Vehicle Entry": '{% trans "Registrar Entrada de Vehículo" %}',
    "Select Tariff": '{% trans "Seleccionar Tarifa" %}',
    "Select Parking Spot": '{% trans "Seleccionar Plaza" %}',
    "Cancel": '{% trans "Cancelar" %}',
    "Confirm Entry": '{% trans "Confirmar Entrada" %}',
    
    # Check out
    "Process Vehicle Exit": '{% trans "Procesar Salida de Vehículo" %}',
    "Current Session Details": '{% trans "Detalles de la Sesión Actual" %}',
    "Entry Time:": '{% trans "Hora de Entrada:" %}',
    "Duration:": '{% trans "Duración:" %}',
    "hours": '{% trans "horas" %}',
    "Parking Spot:": '{% trans "Plaza de Parking:" %}',
    "Applied Tariff:": '{% trans "Tarifa Aplicada:" %}',
    "Estimated Amount": '{% trans "Importe Estimado" %}',
    "Process Check-Out": '{% trans "Procesar Salida" %}',
    
    # Parking list
    "Manage Parkings": '{% trans "Gestionar Parkings" %}',
    "Active": '{% trans "Activo" %}',
    "Inactive": '{% trans "Inactivo" %}',
    "Edit": '{% trans "Editar" %}',
    "Close": '{% trans "Cerrar" %}',
    "Save": '{% trans "Guardar" %}',
    "Create New Parking": '{% trans "Crear Nuevo Parking" %}',
    "Name": '{% trans "Nombre" %}',
    "Address": '{% trans "Dirección" %}',
    
    # Rates
    "Financial Overview": '{% trans "Resumen Financiero" %}',
    "Monthly Revenue": '{% trans "Ingresos Mensuales" %}',
    "Pending Payments": '{% trans "Pagos Pendientes" %}',
    "Action Required": '{% trans "Acción Requerida" %}',
    "Active Tariffs": '{% trans "Tarifas Activas" %}',
    "Type": '{% trans "Tipo" %}',
    "Rate": '{% trans "Tarifa" %}',
    "Recent Transactions": '{% trans "Transacciones Recientes" %}',
    "Amount": '{% trans "Importe" %}',
    "Pricing Configuration": '{% trans "Configuración de Precios" %}',
    "Weekend Surcharge (%)": '{% trans "Recargo de Fin de Semana (%)" %}',
    "Special Event Multiplier (x)": '{% trans "Multiplicador de Evento Especial (x)" %}',
    "Enable Dynamic Pricing": '{% trans "Habilitar Precios Dinámicos" %}',
    "Apply Configuration": '{% trans "Aplicar Configuración" %}',
    
    # Space management
    "Interactive Map": '{% trans "Mapa Interactivo" %}',
    "Filters": '{% trans "Filtros" %}',
    "Floor": '{% trans "Planta" %}',
    "All Floors": '{% trans "Todas las Plantas" %}',
    "Status": '{% trans "Estado" %}',
    "All Status": '{% trans "Todos los Estados" %}',
    "Free": '{% trans "Libre" %}',
    "Occupied": '{% trans "Ocupado" %}',
    "Reserved": '{% trans "Reservado" %}',
    "Apply Filters": '{% trans "Aplicar Filtros" %}',
    
    # Vehicle registry
    "Active Vehicles": '{% trans "Vehículos Activos" %}',
    "Search License Plate": '{% trans "Buscar Matrícula" %}',
    "All Vehicles": '{% trans "Todos los Vehículos" %}',
    "Overstay Alert": '{% trans "Alerta de Exceso de Tiempo" %}',
    "VIP Only": '{% trans "Solo VIP" %}',
    "Tariff": '{% trans "Tarifa" %}',
    "Actions": '{% trans "Acciones" %}',
    "Previous": '{% trans "Anterior" %}',
    "Next": '{% trans "Siguiente" %}',
    
    # Vehicle search
    "Vehicle Lookup": '{% trans "Búsqueda de Vehículo" %}',
    "Enter License Plate": '{% trans "Introducir Matrícula" %}',
    "Search": '{% trans "Buscar" %}',
    "Scan with Camera": '{% trans "Escanear con Cámara" %}',
    
    # Analytics
    "Analytics & Reports": '{% trans "Analíticas y Reportes" %}',
    "Vehicle History": '{% trans "Historial del Vehículo" %}',
    "Top 10 Most Used Spots": '{% trans "Top 10 Plazas Más Usadas" %}',
    "Historical Occupancy": '{% trans "Ocupación Histórica" %}',
    "Check Occupancy": '{% trans "Comprobar Ocupación" %}',
    "Uses": '{% trans "Usos" %}',
}

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for text, translated in translations.items():
        if text == "Terminal A - Principal":
            continue
        content = content.replace(text, translated)
        
    # Quick fix for duplicated translations if run multiple times
    content = content.replace('{% trans "{% trans "', '{% trans "')
    content = content.replace('" %}" %}', '" %}')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("Translated templates.")
