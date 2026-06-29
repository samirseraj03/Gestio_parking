import os
import re

ca_translations = {
    "Dashboard": "Tauler",
    "Buscador": "Cercador",
    "Space Management": "Gestió d'Espais",
    "Vehicle Registry": "Registre de Vehicles",
    "Analíticas": "Analítiques",
    "Terminal A - Principal": "Terminal A - Principal",
    "Visión General del Dashboard": "Visió General del Tauler",
    "Métricas en tiempo real para": "Mètriques en temps real per a",
    "Ocupación Actual": "Ocupació Actual",
    "Ingresos Diarios": "Ingressos Diaris",
    "vs. día anterior": "vs. dia anterior",
    "Alertas Activas": "Alertes Actives",
    "Requiere atención": "Requereix atenció",
    "Actividad Reciente": "Activitat Recent",
    "Hora": "Hora",
    "Evento": "Esdeveniment",
    "No hay actividad reciente.": "No hi ha activitat recent.",
    "Editar": "Editar",
    "Cancelar": "Cancel·lar",
    "Resumen Financiero": "Resum Financer",
    "Ingresos Mensuales": "Ingressos Mensuals",
    "Pagos Pendientes": "Pagaments Pendents",
    "Configuración de Precios": "Configuració de Preus",
    "Recargo de Fin de Semana (%)": "Recàrrec de Cap de Setmana (%)",
    "Transacciones Recientes": "Transaccions Recents",
    "Importe": "Import",
    "Filtros": "Filtres",
    "Planta": "Planta",
    "Ocupado": "Ocupat",
    "Reservado": "Reservat",
    "Buscar": "Cercar",
    "Plaza reservada con éxito.": "Plaça reservada amb èxit.",
    "Plaza liberada con éxito.": "Plaça alliberada amb èxit.",
    "Error al modificar plaza: %(error)s": "Error en modificar la plaça: %(error)s",
    "Configuración de precios aplicada correctamente.": "Configuració de preus aplicada correctament.",
    "Parking %(name)s actualizado correctamente.": "Pàrquing %(name)s actualitzat correctament.",
    "Parking %(name)s creado correctamente.": "Pàrquing %(name)s creat correctament.",
    "Error en parking: %(error)s": "Error en el pàrquing: %(error)s",
    "Por favor introduce una matrícula.": "Si us plau, introdueix una matrícula.",
    "Entrada registrada para %(plate)s.": "Entrada registrada per a %(plate)s.",
    "Error al registrar entrada: %(error)s": "Error en registrar l'entrada: %(error)s",
    "Salida y cobro procesado correctamente para %(plate)s.": "Sortida i cobrament processat correctament per a %(plate)s.",
    "Error al procesar salida: %(error)s": "Error en processar la sortida: %(error)s",
    "🟢 Libre": "🟢 Lliure",
    "🔴 Ocupado": "🔴 Ocupat",
    "🔵 Reservado": "🔵 Reservat",
    "Básico": "Bàsic",
    "Premium": "Premium",
    "Mensual": "Mensual",
    "Nombre": "Nom",
    "Dirección": "Adreça",
    "Activo": "Actiu",
    "Parking": "Pàrquing",
    "Parkings": "Pàrquings",
    "Nombre del nivel": "Nom del nivell",
    "Número de planta": "Número de planta",
    "Descripción": "Descripció",
    "Nivel": "Nivell",
    "Niveles": "Nivells",
    "Número de plaza": "Número de plaça",
    "Estado": "Estat",
    "Plaza de aparcamiento": "Plaça d'aparcament",
    "Plazas de aparcamiento": "Places d'aparcament",
    "Nombre de la tarifa": "Nom de la tarifa",
    "Tipo de tarifa": "Tipus de tarifa",
    "Precio por hora (€)": "Preu per hora (€)",
    "Precio por mes (€)": "Preu per mes (€)",
    "Activa": "Activa",
    "Tarifa": "Tarifa",
    "Tarifas": "Tarifes",
    "Matrícula": "Matrícula",
    "Hora de entrada": "Hora d'entrada",
    "Hora de salida": "Hora de sortida",
    "Plaza": "Plaça",
    "Tarifa aplicada": "Tarifa aplicada",
    "Importe total (€)": "Import total (€)",
    "Sesión de vehículo": "Sessió de vehicle",
    "Sesiones de vehículos": "Sessions de vehicles",
}

en_translations = {
    "Dashboard": "Dashboard",
    "Buscador": "Search",
    "Space Management": "Space Management",
    "Vehicle Registry": "Vehicle Registry",
    "Analíticas": "Analytics",
    "Terminal A - Principal": "Terminal A - Main",
    "Visión General del Dashboard": "Dashboard Overview",
    "Métricas en tiempo real para": "Real-time metrics for",
    "Ocupación Actual": "Live Occupancy",
    "Ingresos Diarios": "Daily Revenue",
    "vs. día anterior": "vs. previous day",
    "Alertas Activas": "Active Alerts",
    "Requiere atención": "Requires attention",
    "Actividad Reciente": "Recent Activity",
    "Hora": "Time",
    "Evento": "Event",
    "No hay actividad reciente.": "No recent activity.",
    "Editar": "Edit",
    "Cancelar": "Cancel",
    "Resumen Financiero": "Financial Overview",
    "Ingresos Mensuales": "Monthly Revenue",
    "Pagos Pendientes": "Pending Payments",
    "Configuración de Precios": "Pricing Configuration",
    "Recargo de Fin de Semana (%)": "Weekend Surcharge (%)",
    "Transacciones Recientes": "Recent Transactions",
    "Importe": "Amount",
    "Filtros": "Filters",
    "Planta": "Floor",
    "Ocupado": "Occupied",
    "Reservado": "Reserved",
    "Buscar": "Search",
    "Plaza reservada con éxito.": "Spot reserved successfully.",
    "Plaza liberada con éxito.": "Spot freed successfully.",
    "Error al modificar plaza: %(error)s": "Error modifying spot: %(error)s",
    "Configuración de precios aplicada correctamente.": "Pricing configuration applied successfully.",
    "Parking %(name)s actualizado correctamente.": "Parking %(name)s updated successfully.",
    "Parking %(name)s creado correctamente.": "Parking %(name)s created successfully.",
    "Error en parking: %(error)s": "Parking error: %(error)s",
    "Por favor introduce una matrícula.": "Please enter a license plate.",
    "Entrada registrada para %(plate)s.": "Entry registered for %(plate)s.",
    "Error al registrar entrada: %(error)s": "Error registering entry: %(error)s",
    "Salida y cobro procesado correctamente para %(plate)s.": "Exit and payment processed successfully for %(plate)s.",
    "Error al procesar salida: %(error)s": "Error processing exit: %(error)s",
    "🟢 Libre": "🟢 Free",
    "🔴 Ocupado": "🔴 Occupied",
    "🔵 Reservado": "🔵 Reserved",
    "Básico": "Basic",
    "Premium": "Premium",
    "Mensual": "Monthly",
    "Nombre": "Name",
    "Dirección": "Address",
    "Activo": "Active",
    "Parking": "Parking",
    "Parkings": "Parkings",
    "Nombre del nivel": "Level Name",
    "Número de planta": "Floor Number",
    "Descripción": "Description",
    "Nivel": "Level",
    "Niveles": "Levels",
    "Número de plaza": "Spot Number",
    "Estado": "Status",
    "Plaza de aparcamiento": "Parking Spot",
    "Plazas de aparcamiento": "Parking Spots",
    "Nombre de la tarifa": "Tariff Name",
    "Tipo de tarifa": "Tariff Type",
    "Precio por hora (€)": "Price per hour (€)",
    "Precio por mes (€)": "Price per month (€)",
    "Activa": "Active",
    "Tarifa": "Tariff",
    "Tarifas": "Tariffs",
    "Matrícula": "License Plate",
    "Hora de entrada": "Entry Time",
    "Hora de salida": "Exit Time",
    "Plaza": "Spot",
    "Tarifa aplicada": "Applied Tariff",
    "Importe total (€)": "Total Amount (€)",
    "Sesión de vehículo": "Vehicle Session",
    "Sesiones de vehículos": "Vehicle Sessions",
}

def process_po_file(filepath, translations):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found!")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out_lines.append(line)
        if line.startswith('msgid "'):
            msgid = line[7:-2].replace('\\"', '"') # extract text between quotes
            if msgid in translations:
                # the next line should be msgstr ""
                if i+1 < len(lines) and lines[i+1].startswith('msgstr ""'):
                    i += 1
                    translated_str = translations[msgid].replace('"', '\\"')
                    out_lines.append(f'msgstr "{translated_str}"\n')
        i += 1
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out_lines)

process_po_file('locale/ca/LC_MESSAGES/django.po', ca_translations)
process_po_file('locale/en/LC_MESSAGES/django.po', en_translations)
print("Updated .po files.")
