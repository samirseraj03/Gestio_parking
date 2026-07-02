from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext as _
import math

from parking import selectors, services
from parking.services import ParkingServiceError

class DashboardView(TemplateView):
    """
    Thin View para renderizar el Dashboard.
    La vista no hace ningún cálculo, delega toda la extracción de datos a los Selectors.
    """
    template_name = "parking/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "dashboard"
        
        # 1. Obtener datos a través de los selectores (Read-only logic)
        context["occupancy"] = selectors.get_occupancy_stats()
        context["daily_revenue"] = selectors.get_daily_revenue()
        context["revenue_growth"] = selectors.get_daily_revenue_growth()
        context["recent_activity"] = selectors.get_recent_activity(limit=5)
        
        # 2. Las alertas no tienen modelo aún, las inicializamos vacías por ahora
        context["active_alerts"] = []
        
        return context

class SpaceManagementView(TemplateView):
    """
    Thin View para el mapa interactivo de plazas.
    Recibe filtros por GET y delega la construcción de la cuadrícula a selectors.py.
    """
    template_name = "parking/space_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "space_management"
        
        # 1. Capturar parámetros de búsqueda/filtrado desde la URL (ej: ?floor=1&status=occupied)
        floor = self.request.GET.get("floor")
        status = self.request.GET.get("status")
        
        # 2. Delegar la consulta compleja al Selector
        context["levels_with_spots"] = selectors.get_spots_by_level(floor=floor, status=status)
        
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        spot_id = request.POST.get("spot_id")
        try:
            if action == "reserve":
                services.reserve_spot(spot_id=int(spot_id))
                messages.success(request, _("Plaza reservada con éxito."))
            elif action == "free":
                services.cancel_reservation(spot_id=int(spot_id))
                messages.success(request, _("Plaza liberada con éxito."))
        except Exception as e:
            from django.contrib import messages
            messages.error(request, _("Error al modificar plaza: %(error)s") % {'error': e})
            
        from django.urls import reverse
        from django.shortcuts import redirect
        redirect_url = reverse("space_management")
        query_string = request.GET.urlencode()
        if query_string:
            redirect_url = f"{redirect_url}?{query_string}"
        return redirect(redirect_url)

class VehicleRegistryView(TemplateView):
    """
    Thin View para el registro de vehículos activos.
    Recibe los parámetros de búsqueda/filtrado y la paginación.
    """
    template_name = "parking/vehicle_registry.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "vehicle_registry"
        
        # 1. Obtener parámetros de la petición HTTP
        search = self.request.GET.get("search", "")
        status_filter = self.request.GET.get("status_filter", "all") # 'all', 'overstay', 'vip'
        page_number = self.request.GET.get("page", 1)
        
        # 2. Delegar la construcción del QuerySet al Selector
        vehicles_qs = selectors.get_filtered_active_vehicles(
            search=search, 
            status_filter=status_filter
        )
        
        # 3. La paginación es responsabilidad de la capa de presentación (Vista/HTTP)
        paginator = Paginator(vehicles_qs, 15)  # 15 items por página
        page_obj = paginator.get_page(page_number)
        
        context["page_obj"] = page_obj
        context["total_vehicles"] = paginator.count
        
        return context

class RatesBillingView(TemplateView):
    """
    Thin View para visualizar métricas financieras, tarifas y procesar cambios de configuración.
    Separa claramente la lectura (GET) de la escritura (POST).
    """
    template_name = "parking/rates_billing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "rates_billing"
        
        # --- LECTURA (Delegada a Selectores) ---
        context["monthly_revenue"] = selectors.get_current_monthly_revenue()
        context["revenue_growth"] = selectors.get_monthly_revenue_growth()
        context["pending_payments"] = selectors.get_pending_payments_stats()
        context["tariffs"] = selectors.get_active_tariffs()
        context["recent_transactions"] = selectors.get_recent_transactions(limit=10)
        
        return context

    def post(self, request, *args, **kwargs):
        """
        Recibe el formulario de 'Pricing Configuration'.
        No contiene lógica de negocio, solo extrae datos y maneja excepciones.
        """
        # Extraer parámetros de la capa HTTP
        weekend_surcharge = request.POST.get("weekend_surcharge")
        event_multiplier = request.POST.get("event_multiplier")
        is_dynamic = request.POST.get("dynamic_pricing") == "on"
        
        try:
            # --- ESCRITURA (Delegada a Servicios) ---
            services.update_pricing_configuration(
                weekend_surcharge=weekend_surcharge,
                event_multiplier=event_multiplier,
                is_dynamic=is_dynamic
            )
            messages.success(request, _("Configuración de precios aplicada correctamente."))
        except ParkingServiceError as e:
            # Manejo centralizado de errores del servicio
            messages.error(request, str(e))
            
        return redirect("rates_billing")

class ParkingListView(TemplateView):
    template_name = "parking/parking_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "parking_list"
        context['parkings'] = selectors.get_active_parkings()
        return context
        
    def post(self, request, *args, **kwargs):
        """Maneja la creación y edición de parkings"""
        action = request.POST.get('action', 'create')
        name = request.POST.get('name')
        address = request.POST.get('address')
        
        try:
            if action == 'edit':
                parking_id = request.POST.get('parking_id')
                services.update_parking(int(parking_id), name, address, True)
                messages.success(request, _("Parking %(name)s actualizado correctamente.") % {'name': name})
            else:
                services.create_parking(name=name, address=address)
                messages.success(request, _("Parking %(name)s creado correctamente.") % {'name': name})
        except Exception as e:
            messages.error(request, _("Error en parking: %(error)s") % {'error': e})
            
        return redirect('parking_list')

from django.views.generic import FormView, View
from django.urls import reverse

class VehicleSearchView(TemplateView):
    """Controlador central para buscar un vehículo por matrícula y decidir el flujo."""
    template_name = "parking/vehicle_search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "vehicle_search"
        return context

    def post(self, request, *args, **kwargs):
        license_plate = request.POST.get("license_plate", "").strip().upper()
        if not license_plate:
            messages.error(request, _("Por favor introduce una matrícula."))
            return redirect("vehicle_search")
            
        # Preguntar al selector si el coche está dentro
        active_sessions = selectors.get_filtered_active_vehicles(search=license_plate)
        if active_sessions.exists():
            # Si existe, vamos a Salida (Check-Out)
            return redirect("checkout", plate=license_plate)
        else:
            # Si no existe, vamos a Entrada (Check-In)
            return redirect("checkin", plate=license_plate)

class CheckInView(TemplateView):
    """Vista para gestionar la entrada de un vehículo nuevo."""
    template_name = "parking/check_in.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "vehicle_search"
        plate = self.kwargs.get("plate")
        context["license_plate"] = plate
        context["tariffs"] = selectors.get_active_tariffs()
        context["free_spots"] = selectors.get_free_spots()
        return context

    def post(self, request, *args, **kwargs):
        plate = self.kwargs.get("plate")
        spot_id = request.POST.get("spot_id")
        tariff_id = request.POST.get("tariff_id")
        
        try:
            services.check_in_vehicle(plate, int(spot_id), int(tariff_id))
            messages.success(request, _("Entrada registrada para %(plate)s.") % {'plate': plate})
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, _("Error al registrar entrada: %(error)s") % {'error': e})
            return redirect("checkin", plate=plate)

from django.utils import timezone

class CheckOutView(TemplateView):
    template_name = "parking/check_out.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "vehicle_search"
        plate = self.kwargs.get("plate")
        context["license_plate"] = plate
        
        # Obtener sesión activa
        active_sessions = selectors.get_filtered_active_vehicles(search=plate)
        if active_sessions.exists():
            session = active_sessions.first()
            context["session"] = session
            
            # Calcular tiempo transcurrido "simulado" para la vista
            now = timezone.now()
            duration = now - session.entry_time
            total_seconds = duration.total_seconds()
            hours = max(1, math.ceil(total_seconds / 3600))
            
            context["duration_hours"] = hours
            if session.tariff.tariff_type == 'monthly':
                context["estimated_amount"] = session.tariff.price_per_month
            else:
                context["estimated_amount"] = session.tariff.price_per_hour * hours
                
        return context
        
    def post(self, request, *args, **kwargs):
        session_id = request.POST.get("session_id")
        plate = self.kwargs.get("plate")
        try:
            services.checkout_vehicle(int(session_id))
            messages.success(request, _("Salida y cobro procesado correctamente para %(plate)s.") % {'plate': plate})
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, _("Error al procesar salida: %(error)s") % {'error': e})
            return redirect("checkout", plate=plate)

from django.utils.dateparse import parse_datetime

class AnalyticsView(TemplateView):
    """Módulo de Consultas y Auditoría"""
    template_name = "parking/analytics.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_page"] = "analytics"
        
        # Historial por matrícula
        search_plate = self.request.GET.get("plate")
        if search_plate:
            context["vehicle_history"] = selectors.get_vehicle_history(search_plate)
            context["search_plate"] = search_plate
            
        # Ocupación en fecha pasada
        target_date_str = self.request.GET.get("target_datetime")
        if target_date_str:
            try:
                # Expects format YYYY-MM-DDTHH:MM
                target_date = parse_datetime(target_date_str)
                if target_date:
                    context["historical_occupancy"] = selectors.get_historical_occupancy(target_date)
                    context["target_datetime"] = target_date_str
            except Exception:
                pass
                
        # Top 10 plazas
        context["top_spots"] = selectors.get_top_spots(10)
        
        return context
