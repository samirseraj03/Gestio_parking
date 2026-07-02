"""
ParkControl Pro — Seed de Datos Iniciales (Idempotente)

Este script se ejecuta automáticamente al arrancar Docker.
Usa get_or_create para garantizar que los datos se insertan UNA SOLA VEZ.
En ejecuciones posteriores, detecta que los datos ya existen y no duplica nada.
"""

import os
import django
from decimal import Decimal
from django.utils import timezone
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from parking.models import Parking, Level, ParkingSpot, Tariff, VehicleSession, TariffType, SpotStatus


def run_seed():
    print("🔍 Verificando datos iniciales...")
    created_count = 0

    # ─── 1. TARIFAS (siempre se crean si no existen) ───
    basic_tariff, created = Tariff.objects.get_or_create(
        tariff_type=TariffType.BASIC,
        defaults={
            'name': 'Tarifa Básica',
            'price_per_hour': Decimal("4.00"),
            'price_per_month': Decimal("0.00"),
            'is_active': True,
        }
    )
    if created:
        created_count += 1
        print("  ✅ Tarifa Básica creada (4.00€/h)")

    premium_tariff, created = Tariff.objects.get_or_create(
        tariff_type=TariffType.PREMIUM,
        defaults={
            'name': 'Tarifa Premium',
            'price_per_hour': Decimal("8.00"),
            'price_per_month': Decimal("0.00"),
            'is_active': True,
        }
    )
    if created:
        created_count += 1
        print("  ✅ Tarifa Premium creada (8.00€/h)")

    monthly_tariff, created = Tariff.objects.get_or_create(
        tariff_type=TariffType.MONTHLY,
        defaults={
            'name': 'Tarifa Mensual',
            'price_per_hour': Decimal("0.00"),
            'price_per_month': Decimal("250.00"),
            'is_active': True,
        }
    )
    if created:
        created_count += 1
        print("  ✅ Tarifa Mensual creada (250.00€/mes)")

    # ─── 2. PARKING ───
    main_parking, created = Parking.objects.get_or_create(
        name="Terminal A - Principal",
        defaults={'address': "Av. Aeropuerto 123"}
    )
    if created:
        created_count += 1
        print("  ✅ Parking 'Terminal A - Principal' creado")

    # ─── 3. NIVELES ───
    level1, created = Level.objects.get_or_create(
        parking=main_parking,
        floor_number=1,
        defaults={'name': "Nivel 1"}
    )
    if created:
        created_count += 1
        print("  ✅ Nivel 1 creado")

    level2, created = Level.objects.get_or_create(
        parking=main_parking,
        floor_number=2,
        defaults={'name': "Nivel 2"}
    )
    if created:
        created_count += 1
        print("  ✅ Nivel 2 creado")

    # ─── 4. PLAZAS ───
    spots_created = 0
    for level in [level1, level2]:
        for i in range(1, 11):
            _, created = ParkingSpot.objects.get_or_create(
                level=level,
                number=i,
                defaults={'status': SpotStatus.FREE}
            )
            if created:
                spots_created += 1
    if spots_created > 0:
        created_count += spots_created
        print(f"  ✅ {spots_created} plazas de aparcamiento creadas")

    # ─── RESUMEN ───
    if created_count == 0:
        print("ℹ️  Base de datos ya contiene datos iniciales. Sin cambios.")
    else:
        print(f"🎉 Seed completado: {created_count} registros creados.")


if __name__ == '__main__':
    run_seed()
