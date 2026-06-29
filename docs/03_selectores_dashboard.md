# 03 — Selectores y Dashboard (Lógica de Lectura)

## Principio: Separación Comando/Consulta (CQS)

Los selectores son funciones de **solo lectura**. No mutan la base de datos. Esto permite:
- **Cachear** resultados sin riesgo de inconsistencias.
- **Reutilizar** la misma consulta en diferentes vistas/endpoints.
- **Optimizar** con índices y agregaciones sin afectar la lógica de negocio.

## Funciones Implementadas

### Métricas de Ocupación

| Función | Firma | Descripción |
|---------|-------|-------------|
| `get_occupancy_percentage` | `() -> float` | Porcentaje global de ocupación (0.0–100.0) |
| `get_occupancy_by_level` | `() -> QuerySet` | Ocupación desglosada por nivel/planta |
| `get_free_spots` | `(level_id: int \| None) -> QuerySet[ParkingSpot]` | Plazas libres, con filtro opcional por nivel |

### Métricas de Ingresos

| Función | Firma | Descripción |
|---------|-------|-------------|
| `get_daily_revenue` | `(date: date \| None) -> Decimal` | Ingresos totales de un día (por defecto hoy) |
| `get_monthly_revenue` | `(year: int, month: int) -> Decimal` | Ingresos totales de un mes |

### Consultas de Vehículos

| Función | Firma | Descripción |
|---------|-------|-------------|
| `get_active_vehicles` | `(search: str \| None) -> QuerySet[VehicleSession]` | Vehículos dentro del parking, con búsqueda por matrícula |
| `get_vehicle_history` | `(license_plate: str, limit: int \| None) -> QuerySet[VehicleSession]` | Historial de estacionamientos por matrícula |
| `get_spot_history` | `(spot_id: int, limit: int \| None) -> QuerySet[VehicleSession]` | Historial de una plaza específica |
| `get_top_occupied_spots` | `(limit: int = 10) -> QuerySet` | Top N plazas más utilizadas |
| `get_occupied_spots_at_datetime` | `(target_datetime: datetime) -> QuerySet[VehicleSession]` | Plazas ocupadas en un momento del pasado |

## Detalle de Consultas ORM

### `get_occupancy_percentage()`

```python
# Cuenta total de plazas y filtra las ocupadas
total = ParkingSpot.objects.count()
occupied = ParkingSpot.objects.filter(status=SpotStatus.OCCUPIED).count()
return (occupied / total) * 100
```

Utiliza el índice en `ParkingSpot.status` para un conteo rápido.

### `get_daily_revenue(date)`

```python
# Agrega el importe total de sesiones cerradas en un día
VehicleSession.objects.filter(
    exit_time__date=date,
    total_amount__gt=0,
).aggregate(revenue=Coalesce(Sum("total_amount"), Decimal("0.00")))
```

Usa `Coalesce` para retornar `0.00` en vez de `None` cuando no hay datos.

### `get_active_vehicles(search)`

```python
# Filtra sesiones sin hora de salida + búsqueda parcial
VehicleSession.objects.filter(
    exit_time__isnull=True,
).filter(
    license_plate__icontains=search,  # si search != None
).select_related("parking_spot", "parking_spot__level", "tariff")
```

Usa `select_related` para precargar relaciones y evitar N+1 queries.

### `get_occupied_spots_at_datetime(target_datetime)`

```python
# Consulta temporal: ¿quién estaba aparcado en ese momento?
VehicleSession.objects.filter(
    entry_time__lte=target_datetime,
).filter(
    Q(exit_time__gt=target_datetime) | Q(exit_time__isnull=True),
)
```

Replica la funcionalidad de "plazas ocupadas en una fecha/hora" del sistema anterior.

## Código

El código completo está en [`parking/selectors.py`](file:///home/samir/Repositorios/Gestio_parking/parking/selectors.py).

### Mapeo con el sistema anterior

| Funcionalidad antigua | Selector nuevo |
|----------------------|----------------|
| SQL crudo en `busqueda_coche()` | `get_active_vehicles(search)` |
| Consulta de plazas `estado = 'NO'` | `get_free_spots()` |
| Consulta de plazas `estado = 'SI'` | Inversa de `get_free_spots()` o `get_occupancy_percentage()` |
| Historial per matrícula | `get_vehicle_history(license_plate)` |
| Historial per plaça | `get_spot_history(spot_id)` |
| Top 10 plazas más ocupadas | `get_top_occupied_spots(limit=10)` |
| Plazas ocupadas en fecha/hora | `get_occupied_spots_at_datetime(dt)` |
