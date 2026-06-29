# 01 — Arquitectura y Patrones de Diseño

## Estructura de Carpetas

```
Gestio_parking/
├── parking/                    # App principal de Django
│   ├── __init__.py
│   ├── models.py               # Modelos ORM (solo estructura de datos)
│   ├── services.py             # Lógica de ESCRITURA y reglas de negocio
│   ├── selectors.py            # Lógica de LECTURA y consultas complejas
│   ├── admin.py                # Registro en Django Admin (futuro)
│   └── migrations/             # Migraciones auto-generadas
│       └── __init__.py
├── docs/                       # Documentación de arquitectura
│   ├── 01_arquitectura_y_patrones.md
│   ├── 02_modelos_orm.md
│   ├── 03_selectores_dashboard.md
│   └── 04_servicios_y_logica.md
└── manage.py                   # (futuro, al inicializar proyecto Django)
```

## Separación de Responsabilidades

| Capa | Archivo | Responsabilidad | Ejemplo |
|------|---------|----------------|---------|
| **Modelos** | `models.py` | Definir la estructura de datos y relaciones. **Nada más.** | `ParkingSpot`, `VehicleSession` |
| **Servicios** | `services.py` | Operaciones que **mutan** la base de datos. Reglas de negocio. | `vehicle_check_in()`, `vehicle_check_out()` |
| **Selectores** | `selectors.py` | Consultas de **solo lectura**. Agregaciones para el dashboard. | `get_occupancy_percentage()`, `get_daily_revenue()` |

## ¿Por qué el Patrón de Capa de Servicios?

### 1. Evita el Antipatrón "Fat Models"

En Django es tentador colocar toda la lógica dentro de los modelos (en métodos como `save()`, `clean()`, o managers personalizados). Esto funciona para casos simples, pero **ParkControl Pro necesita transacciones que afectan a varias tablas simultáneamente**:

- Un **check-in** debe crear un `VehicleSession` **y** cambiar el estado de un `ParkingSpot` a `OCCUPIED`.
- Un **check-out** debe calcular el importe, actualizar la sesión **y** liberar la plaza.

Si esta lógica vive en `VehicleSession.save()`, el modelo necesita conocer y manipular `ParkingSpot`, creando un acoplamiento fuerte entre modelos. Con un **servicio**, la lógica transaccional vive en un lugar centralizado y los modelos permanecen como simples contenedores de datos.

### 2. Transacciones Atómicas Controladas

El decorator `@transaction.atomic` de Django envuelve toda la operación en una transacción SQL. Si algo falla (por ejemplo, la plaza ya está ocupada), **todo se revierte automáticamente**. Esto es crítico para la facturación:

```python
@transaction.atomic
def vehicle_check_out(session_id: int) -> VehicleSession:
    # Si el cálculo del importe falla, la plaza NO se libera
    # → consistencia garantizada
    ...
```

### 3. Testabilidad

Los servicios y selectores son **funciones puras** (reciben parámetros, devuelven resultados). Son fáciles de probar con unit tests sin necesidad de simular peticiones HTTP:

```python
# Test directo, sin necesidad de Client() ni Request()
def test_check_in_creates_session():
    session = vehicle_check_in(
        license_plate="1234ABC",
        spot_id=1,
        tariff_id=1
    )
    assert session.parking_spot.status == SpotStatus.OCCUPIED
```

### 4. Preparación para la API REST

Cuando se añadan las vistas (Django REST Framework), serán **delegadores delgados** que simplemente llaman a servicios y selectores:

```python
# Futuro: vista extremadamente simple
class CheckInView(APIView):
    def post(self, request):
        session = vehicle_check_in(**request.data)  # ← toda la lógica está en el servicio
        return Response(SessionSerializer(session).data)
```

### 5. Escalabilidad del Equipo

Con esta separación, diferentes desarrolladores pueden trabajar en la lógica de negocio (`services.py`), las consultas del dashboard (`selectors.py`) y la capa de presentación (futuras views) **sin conflictos**.

## Selectores: ¿Por qué separarlos de los Servicios?

La razón principal es el **principio de separación comando/consulta (CQS)**:

- **Comandos** (servicios): Cambian el estado del sistema. Pueden fallar. Necesitan transacciones.
- **Consultas** (selectores): Solo leen. Son idempotentes. Se pueden cachear fácilmente.

Para el dashboard de ParkControl Pro, los selectores necesitan hacer agregaciones complejas (`Count`, `Sum`, `Avg`) que no pertenecen ni a los modelos ni a los servicios. Un archivo `selectors.py` dedicado mantiene estas consultas organizadas y optimizadas.
