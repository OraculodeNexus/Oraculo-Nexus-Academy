EL ORÁCULO DE NEXUS ACADEMY — VERSIÓN PREPARADA PARA RENDER
===========================================================

Incluye:
- Página de bienvenida y registro por nombre.
- Cuestionario de 15 preguntas situacionales.
- Asignación automática a Aether, Terra, Ignis o Aqua.
- Registro en SQLite.
- Panel privado de directivos y exportación CSV.
- Diseño adaptable a teléfonos.
- Gunicorn y configuración inicial de Render.

PUBLICACIÓN EN RENDER
1. Sube el contenido de esta carpeta a un repositorio de GitHub.
2. En Render elige New > Blueprint y conecta ese repositorio, o crea un Web Service.
3. Configuración manual: Runtime Python; Build Command: pip install -r requirements.txt;
   Start Command: gunicorn app:app.
4. En Environment configura SECRET_KEY (puedes usar Generate) y ADMIN_PASSWORD
   (elige una contraseña larga que solo conozcan los directivos).
5. Despliega y prueba la página y /directivos.

IMPORTANTE SOBRE LOS RESULTADOS Y EL PLAN GRATUITO
La aplicación usa SQLite. En Render, los servicios gratuitos tienen un sistema de
archivos efímero: la base de datos puede perderse al reiniciar, suspender o volver
a desplegar el servicio. El plan gratuito sirve para probar el cuestionario, pero
NO debe usarse para registrar resultados reales de estudiantes.

Para conservar resultados de forma fiable en Render, hay que conectar una base de
datos PostgreSQL persistente o contratar un servicio web con disco persistente.
La versión actual de este paquete todavía usa SQLite; antes de abrir la selección
real a todos los estudiantes, debemos decidir y configurar el almacenamiento
persistente. No guardes contraseñas ni datos sensibles de estudiantes en el test.

SEGURIDAD
En Render la aplicación no inicia si faltan SECRET_KEY o ADMIN_PASSWORD.
No publiques esas claves en GitHub ni las escribas en archivos del proyecto.

PRUEBA LOCAL
Python 3.10 o superior; instala con pip install -r requirements.txt y ejecuta
python app.py. La clave local de directivos es 'clave-local-solo-para-pruebas'.
Cámbiala usando la variable ADMIN_PASSWORD antes de cualquier uso compartido.

NOTA
La selección es recreativa y no constituye una evaluación psicológica clínica.
Cada nombre se registra una sola vez (sin distinguir mayúsculas/minúsculas).
