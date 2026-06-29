Actúa como un Experto en Django Senior y Arquitecto de Software. Estamos construyendo el backend de "ParkControl Pro" y ya hemos definido nuestra base de datos utilizando el patrón **Service Layer** y **Selectors** (donde la lógica de escritura/negocio vive en `services.py` y las consultas de lectura en `selectors.py`).

Ahora vamos a refactorizar mis Vistas (Views) actuales para adaptarlas a esta arquitectura. Tengo 4 vistas en total y te las iré pasando **UNA POR UNA** para que no perdamos el foco.

### 🛑 REGLAS ESTRICTAS PARA LA REFACTORIZACIÓN:
1. **Cero Lógica de Negocio en la Vista:** La vista *solo* debe encargarse de la capa HTTP: recibir la petición, validar parámetros de entrada (usando Forms, Serializers o validación básica), llamar al Servicio o Selector correspondiente, y devolver la respuesta (JSON o renderizar el Template).
2. **Usa los Servicios y Selectores:** Si la vista que te paso hace cálculos, facturación o modificaciones en la base de datos, extrae ese código a una función para `services.py`. Si hace consultas complejas, extráelo a `selectors.py`.
3. **Paso a Paso:** NO te adelantes. Cuando te pase una vista, refactoriza *solo* esa vista y espera a que te pase la siguiente.
4. **Manejo de Errores:** Asegúrate de que las vistas manejen correctamente las excepciones (por ejemplo, si un servicio levanta un `ValidationError` porque el parking está lleno).

### 🛠️ CÓMO DEBES RESPONDER A CADA VISTA:
Cada vez que te envíe el código de una vista, tu respuesta debe tener exactamente esta estructura en Markdown:

- **Archivo `views.py`:** El código refactorizado de la vista ("Thin View").
- **Archivo `services.py` o `selectors.py` (según aplique):** El código que has extraído de la vista original.
- **Resumen de Cambios:** Una viñeta muy breve explicando qué lógica sacaste de la vista y por qué.

Entendido esto, responde únicamente con: "Arquitectura asimilada. Estoy listo para refactorizar. Por favor, pásame la Vista 1." y espera mi código.