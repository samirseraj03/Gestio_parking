Actúa como un Arquitecto de Software y Experto en Django Senior. Vamos a desarrollar el backend de "ParkControl Pro", un sistema integral de gestión de parkings. 

Tu tarea es diseñar la estructura de la base de datos y la arquitectura del código paso a paso. Para evitar que te pierdas y garantizar la máxima calidad, vas a generar tu respuesta estructurada en 4 bloques que representarán archivos Markdown (`.md`). 

Debes adherirte estrictamente a los siguientes **Guardrails (Interraíles)** durante toda tu respuesta:

### 🛑 REGLAS ESTRICTAS (LO QUE NO PUEDES HACER):
1. **NO** escribas código de Vistas (Views), Serializadores (Serializers), URLs o Templates HTML en esta fase.
2. **NO** utilices SQL crudo. Todo debe estar diseñado pensando en el ORM de Django.
3. **NO** pongas la lógica de negocio (cálculo de tarifas, asignación de plazas) dentro de los Modelos ni de las Vistas.
4. **NO** asumas requerimientos que no estén descritos.

### ✅ REGLAS DE ARQUITECTURA (LO QUE DEBES HACER):
1. **Utiliza el Patrón "Service Layer" y "Selectors"**: Toda la lógica que mute la base de datos (crear un registro de vehículo, facturar) debe ir en un archivo `services.py`. Toda consulta compleja (métricas del dashboard, plazas libres) debe ir en un archivo `selectors.py`.
2. **Tipado Estricto**: Usa Type Hints (`-> int`, `-> QuerySet`) en todas las funciones y métodos que propongas.
3. **Uso de Enums**: Utiliza `models.TextChoices` o `models.IntegerChoices` para los estados (ej. Estado de la plaza, Tipo de tarifa).

---

Por favor, genera la solución estructurada exactamente con los siguientes 4 bloques Markdown:

### Bloque 1: `01_arquitectura_y_patrones.md`
Explica brevemente la estructura de carpetas que usaremos para separar responsabilidades (Models, Services, Selectors). Justifica por qué el Patrón de Capa de Servicios es el mejor refactoring para este caso de uso en Django, especialmente para manejar la facturación y los cambios de estado de las plazas.

### Bloque 2: `02_modelos_orm.md`
Escribe el código en Python (Django ORM) para los modelos de la base de datos. Debes incluir:
- `Level`: Para agrupar las plazas (ej. Planta 1, Planta 2).
- `ParkingSpot`: Relacionado con `Level`. Campos: número, estado (Verde/Libre, Rojo/Ocupado, Azul/Reservado).
- `Tariff`: Tipos de servicio (Básico, Premium, Mensual) y sus precios por hora/mes.
- `VehicleSession`: El registro central. Placa, hora de entrada, hora de salida (nulo si sigue dentro), relación con `ParkingSpot`, relación con `Tariff`, e importe total.
*Asegúrate de incluir índices en los campos más consultados (como la placa del vehículo o el estado de la plaza) para optimizar el dashboard.*

### Bloque 3: `03_selectores_dashboard.md`
Diseña el esqueleto de las funciones en un archivo `selectors.py`. Aquí debe ir la lógica de lectura.
Escribe las firmas de las funciones y la consulta ORM necesaria para:
- Obtener el porcentaje de ocupación actual.
- Obtener los ingresos diarios.
- Listar los vehículos activos (con filtros de búsqueda).

### Bloque 4: `04_servicios_y_logica.md`
Diseña el esqueleto de las funciones en un archivo `services.py`. Aquí debe ir la lógica de escritura y reglas de negocio.
Escribe el código para las siguientes transacciones (asegúrate de usar `transaction.atomic` cuando se modifiquen varias tablas):
- `vehicle_check_in(...)`: Crea una sesión y cambia el estado de la plaza a Rojo.
- `vehicle_check_out(...)`: Calcula el tiempo transcurrido, aplica la tarifa correspondiente, guarda el importe total en la sesión y libera la plaza (Verde).

Comienza tu respuesta generando el Bloque 1.