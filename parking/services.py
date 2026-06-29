"""
ParkControl Pro — Servicios (Lógica de Escritura y Reglas de Negocio)

Funciones que mutan la base de datos y aplican reglas de negocio.
Siguiendo las reglas de arquitectura:
  - Toda mutación pasa por aquí (nunca en modelos ni en vistas).
  - Transacciones atómicas con @transaction.atomic para operaciones multi-tabla.
  - Type Hints estrictos en todas las funciones.
  - Uso exclusivo del ORM de Django (sin SQL crudo).
"""

import math
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from .models import (
    ParkingSpot,
    SpotStatus,
    Tariff,
    TariffType,
    VehicleSession,
)


# =============================================================================
# EXCEPCIONES PERSONALIZADAS
# =============================================================================

class ParkingServiceError(Exception):
    """Excepción base para errores del servicio de parking."""
    pass


class SpotNotAvailableError(ParkingServiceError):
    """La plaza solicitada no está disponible (no está libre)."""
    pass


class SpotNotFoundError(ParkingServiceError):
    """La plaza solicitada no existe."""
    pass


class TariffNotFoundError(ParkingServiceError):
    """La tarifa solicitada no existe o no está activa."""
    pass


class SessionNotFoundError(ParkingServiceError):
    """La sesión de vehículo no existe."""
    pass


class SessionAlreadyClosedError(ParkingServiceError):
    """La sesión ya tiene hora de salida (el vehículo ya salió)."""
    pass


class VehicleAlreadyParkedError(ParkingServiceError):
    """El vehículo ya tiene una sesión activa en el parking."""
    pass


# =============================================================================
# SERVICIOS DE CHECK-IN / CHECK-OUT
# =============================================================================

@transaction.atomic
def vehicle_check_in(
    *,
    license_plate: str,
    spot_id: int,
    tariff_id: int,
) -> VehicleSession:
    """
    Registra la entrada de un vehículo al parking.

    Operaciones atómicas:
      1. Valida que la plaza existe y está libre.
      2. Valida que la tarifa existe y está activa.
      3. Valida que el vehículo no tiene ya una sesión activa.
      4. Crea una nueva VehicleSession con la hora de entrada actual.
      5. Cambia el estado de la plaza a OCCUPIED (🔴).

    Args:
        license_plate: Matrícula del vehículo (ej. "1234ABC").
        spot_id: ID de la plaza donde estacionar.
        tariff_id: ID de la tarifa a aplicar.

    Returns:
        VehicleSession: La sesión de estacionamiento creada.

    Raises:
        SpotNotFoundError: Si la plaza no existe.
        SpotNotAvailableError: Si la plaza no está libre.
        TariffNotFoundError: Si la tarifa no existe o no está activa.
        VehicleAlreadyParkedError: Si el vehículo ya está dentro del parking.
    """
    # 1. Validar y bloquear la plaza (SELECT FOR UPDATE para evitar race conditions)
    try:
        spot: ParkingSpot = (
            ParkingSpot.objects
            .select_for_update()
            .get(id=spot_id)
        )
    except ParkingSpot.DoesNotExist:
        raise SpotNotFoundError(
            f"La plaza con ID {spot_id} no existe."
        )

    if spot.status != SpotStatus.FREE:
        raise SpotNotAvailableError(
            f"La plaza {spot.number} no está disponible. "
            f"Estado actual: {spot.get_status_display()}."
        )

    # 2. Validar la tarifa
    try:
        tariff: Tariff = Tariff.objects.get(id=tariff_id, is_active=True)
    except Tariff.DoesNotExist:
        raise TariffNotFoundError(
            f"La tarifa con ID {tariff_id} no existe o no está activa."
        )

    # 3. Comprobar que el vehículo no está ya dentro
    active_session_exists: bool = VehicleSession.objects.filter(
        license_plate=license_plate,
        exit_time__isnull=True,
    ).exists()

    if active_session_exists:
        raise VehicleAlreadyParkedError(
            f"El vehículo con matrícula '{license_plate}' ya tiene una "
            f"sesión activa en el parking."
        )

    # 4. Crear la sesión de estacionamiento
    session: VehicleSession = VehicleSession.objects.create(
        license_plate=license_plate.upper().strip(),
        entry_time=timezone.now(),
        parking_spot=spot,
        tariff=tariff,
        total_amount=Decimal("0.00"),
    )

    # 5. Cambiar el estado de la plaza a OCCUPIED
    spot.status = SpotStatus.OCCUPIED
    spot.save(update_fields=["status", "updated_at"])

    return session


@transaction.atomic
def vehicle_check_out(*, session_id: int) -> VehicleSession:
    """
    Registra la salida de un vehículo del parking.

    Operaciones atómicas:
      1. Valida que la sesión existe y está activa (sin hora de salida).
      2. Calcula el tiempo transcurrido desde la entrada.
      3. Aplica la tarifa correspondiente para calcular el importe total.
      4. Guarda la hora de salida y el importe en la sesión.
      5. Libera la plaza (cambia estado a FREE 🟢).

    Args:
        session_id: ID de la sesión de estacionamiento.

    Returns:
        VehicleSession: La sesión actualizada con hora de salida e importe.

    Raises:
        SessionNotFoundError: Si la sesión no existe.
        SessionAlreadyClosedError: Si la sesión ya fue cerrada (ya tiene hora de salida).
    """
    # 1. Obtener y bloquear la sesión
    try:
        session: VehicleSession = (
            VehicleSession.objects
            .select_for_update()
            .select_related("parking_spot", "tariff")
            .get(id=session_id)
        )
    except VehicleSession.DoesNotExist:
        raise SessionNotFoundError(
            f"La sesión con ID {session_id} no existe."
        )

    if session.exit_time is not None:
        raise SessionAlreadyClosedError(
            f"La sesión {session_id} ya fue cerrada el "
            f"{session.exit_time.strftime('%Y-%m-%d %H:%M:%S')}. "
            f"Importe cobrado: {session.total_amount}€."
        )

    # 2. Calcular el tiempo transcurrido
    now = timezone.now()
    duration = now - session.entry_time
    total_seconds: float = duration.total_seconds()

    # 3. Calcular el importe según el tipo de tarifa
    total_amount: Decimal = _calculate_amount(
        tariff=session.tariff,
        total_seconds=total_seconds,
    )

    # 4. Actualizar la sesión
    session.exit_time = now
    session.total_amount = total_amount
    session.save(update_fields=["exit_time", "total_amount", "updated_at"])

    # 5. Liberar la plaza (bloquear para escritura)
    spot: ParkingSpot = (
        ParkingSpot.objects
        .select_for_update()
        .get(id=session.parking_spot_id)
    )
    spot.status = SpotStatus.FREE
    spot.save(update_fields=["status", "updated_at"])

    return session


# =============================================================================
# FUNCIONES INTERNAS DE CÁLCULO
# =============================================================================

def _calculate_amount(*, tariff: Tariff, total_seconds: float) -> Decimal:
    """
    Calcula el importe total según la tarifa y el tiempo transcurrido.

    Reglas de facturación:
      - BASIC / PREMIUM: Se factura por horas completas (redondeo hacia arriba).
        Ej: 2h 15min → se facturan 3 horas.
      - MONTHLY: Se cobra el precio fijo mensual independientemente del tiempo.

    Args:
        tariff: Instancia de Tariff con los precios.
        total_seconds: Segundos totales de estancia.

    Returns:
        Decimal: Importe total redondeado a 2 decimales.
    """
    if tariff.tariff_type == TariffType.MONTHLY:
        # Tarifa mensual: precio fijo
        return tariff.price_per_month

    # Tarifas por hora (BASIC / PREMIUM)
    # Redondear hacia arriba: 2h 1min → 3 horas facturadas
    total_hours: int = math.ceil(total_seconds / 3600)

    # Mínimo 1 hora
    total_hours = max(total_hours, 1)

    amount: Decimal = tariff.price_per_hour * Decimal(str(total_hours))

    # Redondear a 2 decimales
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =============================================================================
# SERVICIOS AUXILIARES
# =============================================================================

@transaction.atomic
def reserve_spot(*, spot_id: int) -> ParkingSpot:
    """
    Reserva una plaza de aparcamiento (cambia estado a RESERVED 🔵).

    Args:
        spot_id: ID de la plaza a reservar.

    Returns:
        ParkingSpot: La plaza actualizada.

    Raises:
        SpotNotFoundError: Si la plaza no existe.
        SpotNotAvailableError: Si la plaza no está libre.
    """
    try:
        spot: ParkingSpot = (
            ParkingSpot.objects
            .select_for_update()
            .get(id=spot_id)
        )
    except ParkingSpot.DoesNotExist:
        raise SpotNotFoundError(
            f"La plaza con ID {spot_id} no existe."
        )

    if spot.status != SpotStatus.FREE:
        raise SpotNotAvailableError(
            f"La plaza {spot.number} no está disponible para reservar. "
            f"Estado actual: {spot.get_status_display()}."
        )

    spot.status = SpotStatus.RESERVED
    spot.save(update_fields=["status", "updated_at"])

    return spot


@transaction.atomic
def cancel_reservation(*, spot_id: int) -> ParkingSpot:
    """
    Cancela la reserva de una plaza (cambia estado de RESERVED a FREE).

    Args:
        spot_id: ID de la plaza reservada.

    Returns:
        ParkingSpot: La plaza actualizada.

    Raises:
        SpotNotFoundError: Si la plaza no existe.
        SpotNotAvailableError: Si la plaza no está en estado RESERVED.
    """
    try:
        spot: ParkingSpot = (
            ParkingSpot.objects
            .select_for_update()
            .get(id=spot_id)
        )
    except ParkingSpot.DoesNotExist:
        raise SpotNotFoundError(
            f"La plaza con ID {spot_id} no existe."
        )

    if spot.status != SpotStatus.RESERVED:
        raise SpotNotAvailableError(
            f"La plaza {spot.number} no está reservada. "
            f"Estado actual: {spot.get_status_display()}."
        )

    spot.status = SpotStatus.FREE
    spot.save(update_fields=["status", "updated_at"])

    return spot

class InvalidConfigurationError(ParkingServiceError):
    pass

@transaction.atomic
def update_pricing_configuration(*, weekend_surcharge: str | int, event_multiplier: str | float, is_dynamic: bool) -> None:
    try:
        surcharge = int(weekend_surcharge)
        multiplier = float(event_multiplier)
    except (ValueError, TypeError):
        raise InvalidConfigurationError("Los valores de configuración deben ser numéricos.")
    if not (0 <= surcharge <= 100):
        raise InvalidConfigurationError("El recargo de fin de semana debe estar entre 0% y 100%.")
    if multiplier < 1.0:
        raise InvalidConfigurationError("El multiplicador de eventos no puede ser menor a 1.0x.")

# =============================================================================
# FUNCIONES AÑADIDAS PARA PARKING CRUD
# =============================================================================
from .models import Parking

@transaction.atomic
def create_parking(name: str, address: str = "") -> Parking:
    return Parking.objects.create(name=name, address=address)

@transaction.atomic
def update_parking(parking_id, name: str, address: str, is_active: bool) -> Parking:
    parking = Parking.objects.get(id=parking_id)
    parking.name = name
    parking.address = address
    parking.is_active = is_active
    parking.save()
    return parking

@transaction.atomic
def delete_parking(parking_id) -> None:
    parking = Parking.objects.get(id=parking_id)
    parking.is_active = False
    parking.save()

# =============================================================================
# FUNCIONES AÑADIDAS PARA FLUJO DE ENTRADA Y SALIDA (BLOQUE 3 Y 4)
# =============================================================================
from django.utils import timezone
from .models import VehicleSession, ParkingSpot, Tariff, SpotStatus

@transaction.atomic
def check_in_vehicle(license_plate: str, spot_id: int, tariff_id: int) -> VehicleSession:
    """Registra la entrada de un vehículo y ocupa la plaza de forma atómica."""
    # select_for_update() asegura que 2 coches no ocupen la misma plaza a la vez
    spot = ParkingSpot.objects.select_for_update().get(id=spot_id)
    
    if spot.status != SpotStatus.FREE:
        raise ParkingServiceError(f"La plaza {spot.number} no está libre.")
        
    tariff = Tariff.objects.get(id=tariff_id)
    
    # Crear la sesión
    session = VehicleSession.objects.create(
        license_plate=license_plate,
        parking_spot=spot,
        tariff=tariff,
        entry_time=timezone.now()
    )
    
    # Actualizar estado de la plaza
    spot.status = SpotStatus.OCCUPIED
    spot.save()
    
    return session

@transaction.atomic
def checkout_vehicle(session_id: int) -> VehicleSession:
    """Procesa la salida de un coche, calculando el precio exacto y liberando la plaza."""
    session = VehicleSession.objects.select_for_update().get(id=session_id)
    
    if session.exit_time is not None:
        raise ParkingServiceError("La sesión ya estaba cerrada.")
        
    now = timezone.now()
    duration = now - session.entry_time
    total_seconds = duration.total_seconds()
    
    # Reutilizamos la función interna _calculate_amount
    total_amount = _calculate_amount(tariff=session.tariff, total_seconds=total_seconds)
    
    session.exit_time = now
    session.total_amount = total_amount
    session.save()
    
    # Liberar plaza
    spot = ParkingSpot.objects.select_for_update().get(id=session.parking_spot_id)
    spot.status = SpotStatus.FREE
    spot.save()
    
    return session
