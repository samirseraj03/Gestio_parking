import os
import django
from decimal import Decimal
from django.utils import timezone
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from parking.models import Parking, Level, ParkingSpot, Tariff, VehicleSession, TariffType, SpotStatus

def run_seed():
    if Parking.objects.exists():
        print("Database already seeded. Skipping.")
        return
        
    print("Seeding database...")
    
    VehicleSession.objects.all().delete()
    
    # 1. Tariffs
    Tariff.objects.all().delete()
    basic_tariff = Tariff.objects.create(tariff_type=TariffType.BASIC, price_per_hour=Decimal("4.00"), is_active=True)
    premium_tariff = Tariff.objects.create(tariff_type=TariffType.PREMIUM, price_per_hour=Decimal("8.00"), is_active=True)
    monthly_tariff = Tariff.objects.create(tariff_type=TariffType.MONTHLY, price_per_hour=Decimal("250.00"), is_active=True)
    # 1.5 Parkings
    Parking.objects.all().delete()
    main_parking = Parking.objects.create(name="Terminal A - Main", address="Av. Aeropuerto 123")
    
    # 2. Levels
    Level.objects.all().delete()
    level1 = Level.objects.create(parking=main_parking, name="Nivel 1", floor_number=1)
    level2 = Level.objects.create(parking=main_parking, name="Nivel 2", floor_number=2)
    
    # 3. Spots
    ParkingSpot.objects.all().delete()
    for i in range(1, 11):
        ParkingSpot.objects.create(level=level1, number=i, status=SpotStatus.FREE)
        ParkingSpot.objects.create(level=level2, number=i, status=SpotStatus.FREE)
        
    # Mark some as occupied or reserved
    spot1 = ParkingSpot.objects.get(level=level1, number=1)
    spot1.status = SpotStatus.OCCUPIED
    spot1.save()
    
    spot2 = ParkingSpot.objects.get(level=level1, number=2)
    spot2.status = SpotStatus.RESERVED
    spot2.save()
    
    spot3 = ParkingSpot.objects.get(level=level2, number=1)
    spot3.status = SpotStatus.OCCUPIED
    spot3.save()
    
    # 4. Sessions
    VehicleSession.objects.all().delete()
    now = timezone.now()
    
    # Active Session 1
    VehicleSession.objects.create(
        license_plate="ABC-1234",
        parking_spot=spot1,
        tariff=basic_tariff,
        entry_time=now - datetime.timedelta(hours=2, minutes=45)
    )
    
    # Active Session 2 (Premium/VIP)
    VehicleSession.objects.create(
        license_plate="DEF-5555",
        parking_spot=spot3,
        tariff=premium_tariff,
        entry_time=now - datetime.timedelta(hours=1, minutes=30)
    )
    
    # Completed Session
    VehicleSession.objects.create(
        license_plate="XYZ-9876",
        parking_spot=ParkingSpot.objects.get(level=level1, number=3),
        tariff=basic_tariff,
        entry_time=now - datetime.timedelta(days=1, hours=3),
        exit_time=now - datetime.timedelta(days=1),
        total_amount=Decimal("12.00")
    )
    
    print("Done!")

if __name__ == '__main__':
    run_seed()
