import requests
import os
from datetime import timedelta

def obtener_distancia_tiempo(origen: tuple, destino: tuple):
    """
    Utiliza la API de Google Maps para obtener la distancia y tiempo estimado
    entre dos puntos usando sus coordenadas.
    
    Args:
        origen: Tuple (latitud, longitud) del punto de origen
        destino: Tuple (latitud, longitud) del punto de destino
        
    Returns:
        Tuple (distancia_km, tiempo_estimado)
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return _calcular_distancia_tiempo_estimado(origen, destino)
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{origen[0]},{origen[1]}",
            "destinations": f"{destino[0]},{destino[1]}",
            "mode": "driving",
            "key": api_key,
            # Incluir hora de salida para considerar tráfico en tiempo real
            "departure_time": "now",
            "traffic_model": "best_guess",
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK":
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                # Convertir metros a kilómetros
                distancia_km = element["distance"]["value"] / 1000
                # Convertir segundos a formato de tiempo
                segundos = element["duration"]["value"]
                tiempo_estimado = str(timedelta(seconds=segundos))
                
                return distancia_km, tiempo_estimado
    
    except Exception as e:
        print(f"Error al consultar Google Maps API: {e}")
    
    # Si hay error o no hay API key, usar el cálculo estimado
    return _calcular_distancia_tiempo_estimado(origen, destino)

def _calcular_distancia_tiempo_estimado(origen, destino):
    """
    Función de respaldo que usa la distancia geodésica para estimar
    cuando no se puede usar Google Maps API.
    """
    from geopy.distance import geodesic
    
    distancia_km = geodesic(origen, destino).km
    # Estimamos 2.5 minutos por kilómetro (velocidad promedio)
    minutos = int(distancia_km * 2.5)
    tiempo_estimado = f"{minutos} mins"
    
    return distancia_km, tiempo_estimado

def calcular_ruta_multiple(origen: tuple, destinos: list):
    """
    Calcula una ruta optimizada con múltiples destinos.
    
    Args:
        origen: Tuple (latitud, longitud) del punto de origen
        destinos: Lista de tuples (latitud, longitud) de los destinos
        
    Returns:
        dict con información de la ruta
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key or not destinos:
        return None
    
    try:
        # Usar Directions API con waypoints
        url = "https://maps.googleapis.com/maps/api/directions/json"
        
        # Convertir destinos a waypoints (todos excepto el último)
        waypoints = []
        for destino in destinos[:-1]:
            waypoints.append(f"{destino[0]},{destino[1]}")
        
        params = {
            "origin": f"{origen[0]},{origen[1]}",
            "destination": f"{destinos[-1][0]},{destinos[-1][1]}",
            "waypoints": "optimize:true|" + "|".join(waypoints),
            "mode": "driving",
            "key": api_key,
            # Parámetros de tráfico
            "departure_time": "now",
            "traffic_model": "best_guess",
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data["status"] == "OK":
            # La respuesta incluye una ruta optimizada
            ruta = data["routes"][0]
            
            # Extraer distancia total
            distancia_total = 0
            duracion_total = 0
            for leg in ruta["legs"]:
                distancia_total += leg["distance"]["value"]
                duracion_total += leg["duration"]["value"]
            
            # Convertir valores
            distancia_km = distancia_total / 1000
            tiempo_estimado = str(timedelta(seconds=duracion_total))
            
            # Obtener el orden optimizado de los waypoints
            orden_optimizado = None
            if "waypoint_order" in ruta:
                orden_optimizado = ruta["waypoint_order"]
            
            return {
                "distancia_km": distancia_km,
                "tiempo_estimado": tiempo_estimado,
                "orden_waypoints": orden_optimizado
            }
    
    except Exception as e:
        print(f"Error al calcular ruta con Google Maps API: {e}")
    
    return None
