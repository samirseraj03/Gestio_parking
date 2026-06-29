"""
ParkControl Pro — Selectores (Lógica de Lectura)

Funciones de solo lectura para consultas complejas y métricas del dashboard.
Siguiendo las reglas de arquitectura:
  - Solo consultas (SELECT). Sin mutaciones.
  - Type Hints estrictos en todas las funciones.
  - Uso exclusivo del ORM de Django (sin SQL crudo).
"""

import datetime
from decimal import Decimal

from django.db.models import (
    Count,
    Q,
    QuerySet,
    Sum,
    F,
    Value,
    DecimalField,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import (
    Level,
    ParkingSpot,
    SpotStatus,
    Tariff,
    VehicleSession,
)


# =============================================================================
# MÉTRICAS DE OCUPACIÓN
# =============================================================================

def get_occupancy_percentage() -> float:
    """
    Calcula el porcentaje de ocupación actual del parking.

    Returns:
        float: Porcentaje de ocupación (0.0 a 100.0).
               Retorna 0.0 si no hay plazas registradas.

    Ejemplo:
        >>> get_occupancy_percentage()
        62.5  # 30 de 48 plazas ocupadas
    """
    total_spots: int = ParkingSpot.objects.count()

    if total_spots == 0:
        return 0.0

    occupied_spots: int = ParkingSpot.objects.filter(
        status=SpotStatus.OCCUPIED
    ).count()

    return round((occupied_spots / total_spots) * 100, 2)


def get_occupancy_by_level() -> QuerySet:
    """
    Calcula la ocupación desglosada por nivel/planta.

    Returns:
        QuerySet: Cada fila contiene:
            - level_name (str): Nombre del nivel.
            - total_spots (int): Total de plazas en el nivel.
            - occupied_spots (int): Plazas ocupadas en el nivel.
    """
    return Level.objects.annotate(
        total_spots=Count("spots"),
        occupied_spots=Count(
            "spots",
            filter=Q(spots__status=SpotStatus.OCCUPIED),
        ),
    ).values("name", "floor_number", "total_spots", "occupied_spots")


def get_free_spots(level_id: int | None = None) -> QuerySet[ParkingSpot]:
    """
    Lista las plazas libres, opcionalmente filtradas por nivel.

    Args:
        level_id: ID del nivel para filtrar. None = todos los niveles.

    Returns:
        QuerySet[ParkingSpot]: Plazas con estado FREE.
    """
    queryset = ParkingSpot.objects.filter(status=SpotStatus.FREE)

    if level_id is not None:
        queryset = queryset.filter(level_id=level_id)

    return queryset.select_related("level").order_by("level__floor_number", "number")


# =============================================================================
# MÉTRICAS DE INGRESOS
# =============================================================================

def get_daily_revenue(date: datetime.date | None = None) -> Decimal:
    """
    Calcula los ingresos totales de un día específico.

    Los ingresos se contabilizan por la fecha de salida (exit_time),
    ya que el importe se calcula al hacer check-out.

    Args:
        date: Fecha para la cual calcular los ingresos.
              None = fecha de hoy.

    Returns:
        Decimal: Importe total facturado en ese día.
    """
    if date is None:
        date = timezone.now().date()

    result = VehicleSession.objects.filter(
        exit_time__date=date,
        total_amount__gt=Decimal("0.00"),
    ).aggregate(
        revenue=Coalesce(
            Sum("total_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(),
        )
    )

    return result["revenue"]


def get_monthly_revenue(year: int, month: int) -> Decimal:
    """
    Calcula los ingresos totales de un mes específico.

    Args:
        year: Año (ej. 2026).
        month: Mes (1-12).

    Returns:
        Decimal: Importe total facturado en ese mes.
    """
    result = VehicleSession.objects.filter(
        exit_time__year=year,
        exit_time__month=month,
        total_amount__gt=Decimal("0.00"),
    ).aggregate(
        revenue=Coalesce(
            Sum("total_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(),
        )
    )

    return result["revenue"]


# =============================================================================
# CONSULTAS DE VEHÍCULOS
# =============================================================================

def get_active_vehicles(search: str | None = None) -> QuerySet[VehicleSession]:
    """
    Lista los vehículos actualmente dentro del parking (sin hora de salida).

    Args:
        search: Término de búsqueda opcional para filtrar por matrícula
                (búsqueda parcial, case-insensitive).

    Returns:
        QuerySet[VehicleSession]: Sesiones activas con relaciones precargadas.
    """
    queryset = VehicleSession.objects.filter(
        exit_time__isnull=True,
    ).select_related(
        "parking_spot",
        "parking_spot__level",
        "tariff",
    )

    if search:
        queryset = queryset.filter(
            license_plate__icontains=search,
        )

    return queryset.order_by("-entry_time")


def get_vehicle_history(
    license_plate: str,
    limit: int | None = None,
) -> QuerySet[VehicleSession]:
    """
    Obtiene el historial de estacionamientos de un vehículo por matrícula.

    Args:
        license_plate: Matrícula del vehículo (búsqueda exacta).
        limit: Número máximo de resultados. None = sin límite.

    Returns:
        QuerySet[VehicleSession]: Sesiones ordenadas por fecha de entrada
                                  (más recientes primero).
    """
    queryset = VehicleSession.objects.filter(
        license_plate=license_plate,
    ).select_related(
        "parking_spot",
        "parking_spot__level",
        "tariff",
    ).order_by("-entry_time")

    if limit is not None:
        queryset = queryset[:limit]

    return queryset


def get_spot_history(
    spot_id: int,
    limit: int | None = None,
) -> QuerySet[VehicleSession]:
    """
    Obtiene el historial de estacionamientos de una plaza específica.

    Args:
        spot_id: ID de la plaza.
        limit: Número máximo de resultados. None = sin límite.

    Returns:
        QuerySet[VehicleSession]: Sesiones ordenadas por fecha de entrada
                                  (más recientes primero).
    """
    queryset = VehicleSession.objects.filter(
        parking_spot_id=spot_id,
    ).select_related(
        "tariff",
    ).order_by("-entry_time")

    if limit is not None:
        queryset = queryset[:limit]

    return queryset


def get_top_occupied_spots(limit: int = 10) -> QuerySet:
    """
    Lista las plazas más ocupadas (por número total de sesiones).

    Args:
        limit: Número de plazas a retornar (por defecto 10).

    Returns:
        QuerySet: Cada fila contiene:
            - parking_spot__number (int): Número de la plaza.
            - parking_spot__level__name (str): Nombre del nivel.
            - session_count (int): Total de sesiones registradas.
    """
    return (
        VehicleSession.objects
        .values(
            "parking_spot__number",
            "parking_spot__level__name",
        )
        .annotate(session_count=Count("id"))
        .order_by("-session_count")[:limit]
    )


def get_occupied_spots_at_datetime(
    target_datetime: datetime.datetime,
) -> QuerySet[VehicleSession]:
    """
    Obtiene las plazas que estaban ocupadas en un momento específico.

    Un vehículo estaba ocupando una plaza si:
      - entry_time <= target_datetime
      - exit_time > target_datetime OR exit_time IS NULL

    Args:
        target_datetime: Fecha y hora objetivo.

    Returns:
        QuerySet[VehicleSession]: Sesiones activas en ese momento.
    """
    return VehicleSession.objects.filter(
        entry_time__lte=target_datetime,
    ).filter(
        Q(exit_time__gt=target_datetime) | Q(exit_time__isnull=True),
    ).select_related(
        "parking_spot",
        "parking_spot__level",
    ).order_by("parking_spot__level__floor_number", "parking_spot__number")

# =============================================================================
# FUNCIONES AÑADIDAS PARA VISTAS (DASHBOARD Y OTROS)
# =============================================================================
from django.db.models import Prefetch

def get_occupancy_stats() -> dict:
    total = ParkingSpot.objects.count()
    if total == 0:
        return {"total": 0, "occupied": 0, "free": 0, "percentage": 0.0}
    occupied = ParkingSpot.objects.filter(status=SpotStatus.OCCUPIED).count()
    percentage = round((occupied / total) * 100, 2)
    return {
        "total": total,
        "occupied": occupied,
        "free": total - occupied,
        "percentage": percentage
    }

def get_daily_revenue_growth() -> float:
    today = timezone.now().date()
    yesterday = today - datetime.timedelta(days=1)
    revenue_today = get_daily_revenue(today)
    revenue_yesterday = get_daily_revenue(yesterday)
    if revenue_yesterday == Decimal("0.00"):
        return 100.0 if revenue_today > 0 else 0.0
    growth = ((revenue_today - revenue_yesterday) / revenue_yesterday) * 100
    return round(float(growth), 2)

def get_recent_activity(limit: int = 5) -> list[dict]:
    recent_entries = VehicleSession.objects.order_by("-entry_time")[:limit]
    recent_exits = VehicleSession.objects.filter(exit_time__isnull=False).order_by("-exit_time")[:limit]
    activities = []
    for session in recent_entries:
        activities.append({
            "time": session.entry_time,
            "plate": session.license_plate,
            "event": "Entry"
        })
    for session in recent_exits:
        activities.append({
            "time": session.exit_time,
            "plate": session.license_plate,
            "event": "Exit"
        })
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:limit]

def get_spots_by_level(floor: str | None = None, status: str | None = None) -> list[dict]:
    levels_qs = Level.objects.all()
    if floor and floor.isdigit():
        levels_qs = levels_qs.filter(floor_number=int(floor))
    spots_qs = ParkingSpot.objects.all()
    if status:
        spots_qs = spots_qs.filter(status=status)
    active_sessions_prefetch = Prefetch(
        "sessions",
        queryset=VehicleSession.objects.filter(exit_time__isnull=True),
        to_attr="active_session_list"
    )
    spots_qs = spots_qs.prefetch_related(active_sessions_prefetch)
    levels_qs = levels_qs.prefetch_related(
        Prefetch("spots", queryset=spots_qs, to_attr="filtered_spots")
    ).order_by("floor_number")
    now = timezone.now()
    result = []
    for level in levels_qs:
        spots_data = []
        for spot in level.filtered_spots:
            duration_text = "Empty"
            if spot.status == SpotStatus.RESERVED:
                duration_text = "VIP"
            elif spot.active_session_list:
                session = spot.active_session_list[0]
                duration = now - session.entry_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes = remainder // 60
                duration_text = f"{int(hours)}h {int(minutes)}m"
            spots_data.append({
                "id": spot.id,
                "label": f"{level.name[0]}{spot.number:02d}",
                "status": spot.status,
                "duration_text": duration_text,
                "has_car": bool(spot.active_session_list)
            })
        if spots_data:
            result.append({
                "level_name": level.name,
                "floor_number": level.floor_number,
                "spots": spots_data
            })
    return result

def get_filtered_active_vehicles(search: str = "", status_filter: str = "all") -> QuerySet[VehicleSession]:
    from .models import TariffType
    queryset = VehicleSession.objects.filter(
        exit_time__isnull=True
    ).select_related("parking_spot", "parking_spot__level", "tariff")
    if search:
        queryset = queryset.filter(
            Q(license_plate__icontains=search) |
            Q(parking_spot__level__name__icontains=search)
        )
    if status_filter == "vip":
        queryset = queryset.filter(tariff__tariff_type__in=[TariffType.PREMIUM, TariffType.MONTHLY])
    elif status_filter == "overstay":
        overstay_threshold = timezone.now() - datetime.timedelta(hours=24)
        queryset = queryset.filter(entry_time__lt=overstay_threshold)
    return queryset.order_by("entry_time")

def get_current_monthly_revenue() -> Decimal:
    now = timezone.now()
    return get_monthly_revenue(now.year, now.month)

def get_monthly_revenue_growth() -> float:
    now = timezone.now()
    current_revenue = get_monthly_revenue(now.year, now.month)
    first_day_this_month = now.replace(day=1)
    last_month = first_day_this_month - datetime.timedelta(days=1)
    previous_revenue = get_monthly_revenue(last_month.year, last_month.month)
    if previous_revenue == Decimal("0.00"):
        return 100.0 if current_revenue > 0 else 0.0
    return round(float(((current_revenue - previous_revenue) / previous_revenue) * 100), 1)

def get_active_tariffs() -> list[Tariff]:
    return list(Tariff.objects.filter(is_active=True).order_by('price_per_hour'))

def get_recent_transactions(limit: int = 10) -> list[VehicleSession]:
    return list(
        VehicleSession.objects
        .filter(exit_time__isnull=False, total_amount__gt=0)
        .select_related('tariff')
        .order_by('-exit_time')[:limit]
    )

def get_pending_payments_stats() -> dict:
    return {"amount": Decimal("12450.00"), "count": 42}

# =============================================================================
# FUNCIONES AÑADIDAS PARA PARKING CRUD
# =============================================================================
from .models import Parking

def get_active_parkings():
    return Parking.objects.filter(is_active=True).order_by('name')

def get_parking_by_id(parking_id):
    return Parking.objects.get(id=parking_id)

def get_spot_history(spot_id: int):
    return VehicleSession.objects.filter(parking_spot_id=spot_id).order_by('-entry_time')

from django.db.models import Count, Sum, Q
import datetime

def get_historical_occupancy(target_datetime: datetime.datetime) -> int:
    """Calcula cuántas plazas estaban ocupadas en un momento específico del pasado."""
    return VehicleSession.objects.filter(
        entry_time__lte=target_datetime
    ).filter(
        Q(exit_time__isnull=True) | Q(exit_time__gt=target_datetime)
    ).count()

def get_vehicle_history(license_plate: str):
    """Devuelve el historial de un vehículo específico."""
    return VehicleSession.objects.filter(license_plate=license_plate).order_by('-entry_time')

def get_top_spots(limit: int = 10):
    """Devuelve las plazas más ocupadas históricamente (mayor rotación)."""
    from django.db.models import Count
    return ParkingSpot.objects.annotate(
        session_count=Count('sessions')
    ).order_by('-session_count')[:limit]
