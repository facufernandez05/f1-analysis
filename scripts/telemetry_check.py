import fastf1
import matplotlib.pyplot as plt

# En Linux, es buena práctica usar rutas relativas o de usuario para el caché
fastf1.Cache.enable_cache("data/")

print("Cargando datos de la sesión...")
# Ejemplo: GP de Miami 2026 (o el más reciente donde haya corrido Franco)
session = fastf1.get_session(2026, "Miami", "Q")
session.load()

# Filtrar por Franco Colapinto (COL)
fastest_col = session.laps.pick_driver("COL").pick_fastest()
telemetry = fastest_col.get_telemetry()

# Graficar algo rápido: Velocidad vs Distancia
plt.plot(telemetry["Distance"], telemetry["Speed"], label="Colapinto")
plt.xlabel("Distancia (m)")
plt.ylabel("Velocidad (km/h)")
plt.title(f"Telemetría de Velocidad - {session.event.EventName}")
plt.legend()
plt.show()
