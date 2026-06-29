"""
ParkControl Pro — Modelos ORM (Django)

Modelos de la base de datos para el sistema de gestión de parkings.
Siguiendo las reglas de arquitectura:
  - Solo estructura de datos y relaciones.
  - Sin lógica de negocio (va en services.py).
  - Enums con TextChoices / IntegerChoices.
  - Índices en los campos más consultados.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal


# =============================================================================
# ENUMS (TextChoices)
# =============================================================================

class SpotStatus(models.TextChoices):
    """Estado de una plaza de aparcamiento."""
    FREE = "free", "🟢 Libre"
    OCCUPIED = "occupied", "🔴 Ocupado"
    RESERVED = "reserved", "🔵 Reservado"


class TariffType(models.TextChoices):
    """Tipo de tarifa de estacionamiento."""
    BASIC = "basic", "Básico"
    PREMIUM = "premium", "Premium"
    MONTHLY = "monthly", "Mensual"


# =============================================================================
# MODELOS
# =============================================================================

import uuid

class Parking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Nombre")
    address = models.CharField(max_length=255, blank=True, verbose_name="Dirección")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "parkings"
        verbose_name = "Parking"
        verbose_name_plural = "Parkings"
        ordering = ["name"]
        
    def __str__(self):
        return self.name

class Level(models.Model):
    parking = models.ForeignKey(Parking, on_delete=models.CASCADE, related_name="levels", null=True, verbose_name="Parking")
    """
    Nivel/planta del parking.
    Agrupa las plazas de aparcamiento por planta.
    """
    name: str = models.CharField(
        max_length=50,
        verbose_name="Nombre del nivel",
        help_text="Ej: Planta 1, Planta -1, Terraza",
    )
    floor_number: int = models.IntegerField(
        verbose_name="Número de planta",
        help_text="Número entero que identifica la planta (0 = planta baja, -1 = sótano, etc.)",
    )
    description: str = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "levels"
        ordering = ["floor_number"]
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"

    def __str__(self) -> str:
        return f"{self.name} (Planta {self.floor_number})"


class ParkingSpot(models.Model):
    """
    Plaza de aparcamiento individual.
    Relacionada con un Level (planta).
    """
    number: int = models.PositiveIntegerField(
        verbose_name="Número de plaza",
    )
    status: str = models.CharField(
        max_length=10,
        choices=SpotStatus.choices,
        default=SpotStatus.FREE,
        verbose_name="Estado",
        db_index=True,  # Índice: campo muy consultado en el dashboard
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name="spots",
        verbose_name="Nivel",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "parking_spots"
        ordering = ["level", "number"]
        verbose_name = "Plaza de aparcamiento"
        verbose_name_plural = "Plazas de aparcamiento"
        constraints = [
            models.UniqueConstraint(
                fields=["level", "number"],
                name="unique_spot_per_level",
            ),
        ]

    def __str__(self) -> str:
        return f"Plaza {self.number} ({self.level.name}) — {self.get_status_display()}"


class Tariff(models.Model):
    """
    Tarifa de estacionamiento.
    Define tipos de servicio (Básico, Premium, Mensual) y sus precios.
    """
    name: str = models.CharField(
        max_length=100,
        verbose_name="Nombre de la tarifa",
        help_text="Ej: Tarifa Básica, Tarifa Premium Fin de Semana",
    )
    tariff_type: str = models.CharField(
        max_length=10,
        choices=TariffType.choices,
        default=TariffType.BASIC,
        verbose_name="Tipo de tarifa",
    )
    price_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Precio por hora (€)",
        help_text="Precio aplicado por hora para tarifas Básica y Premium.",
    )
    price_per_month = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Precio por mes (€)",
        help_text="Precio fijo mensual. Solo aplica para tarifa Mensual.",
    )
    is_active: bool = models.BooleanField(
        default=True,
        verbose_name="Activa",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tariffs"
        ordering = ["tariff_type", "name"]
        verbose_name = "Tarifa"
        verbose_name_plural = "Tarifas"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_tariff_type_display()}) — {self.price_per_hour}€/h"


class VehicleSession(models.Model):
    """
    Registro central de estacionamiento.
    Representa una sesión completa: entrada → (estancia) → salida.
    """
    license_plate: str = models.CharField(
        max_length=20,
        verbose_name="Matrícula",
        db_index=True,  # Índice: búsqueda frecuente por matrícula
    )
    entry_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Hora de entrada",
        db_index=True,  # Índice: consultas de dashboard por fecha
    )
    exit_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Hora de salida",
        help_text="Nulo si el vehículo sigue dentro del parking.",
    )
    parking_spot = models.ForeignKey(
        ParkingSpot,
        on_delete=models.PROTECT,
        related_name="sessions",
        verbose_name="Plaza",
    )
    tariff = models.ForeignKey(
        Tariff,
        on_delete=models.PROTECT,
        related_name="sessions",
        verbose_name="Tarifa aplicada",
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Importe total (€)",
        help_text="Calculado automáticamente al hacer check-out.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vehicle_sessions"
        ordering = ["-entry_time"]
        verbose_name = "Sesión de vehículo"
        verbose_name_plural = "Sesiones de vehículos"
        indexes = [
            models.Index(
                fields=["license_plate", "entry_time"],
                name="idx_plate_entry",
            ),
            models.Index(
                fields=["exit_time"],
                name="idx_exit_time",
                condition=models.Q(exit_time__isnull=True),
            ),
        ]

    def __str__(self) -> str:
        status = "🅿️ Dentro" if self.exit_time is None else "✅ Salido"
        return f"{self.license_plate} — {status} — Plaza {self.parking_spot.number}"

    @property
    def is_active(self) -> bool:
        """Indica si el vehículo sigue dentro del parking."""
        return self.exit_time is None
