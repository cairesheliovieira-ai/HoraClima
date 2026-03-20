import requests
import pytz
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

fuso_por_cidade = {
    'sao paulo': 'America/Sao_Paulo',
    'rio': 'America/Sao_Paulo',
    'tokyo': 'Asia/Tokyo'
}

print("Buscador de Clima e Hora Mundial")
print("-" * 50)

#Nome da cidade
cidade = input("Digite o nome da cidade: ").strip()

geolocator = Nominatim(user_agent="HoraC")

# CORREÇÃO Brasília  ← VOCÊ TEM QUE COLOCAR ISSO!
if "brasilia" in cidade.lower():
    location = geolocator.geocode("Brasília, Brazil")
else:
    location = geolocator.geocode(cidade)
if not location:
    print(f"❌ Cidade '{cidade}' não encontrada!")
else:
    lat = location.latitude
    lon = location.longitude
    print(f"\n📍 Localização: {cidade}")
    print(f"🗺️ Coordenadas: {lat:.2f}, {lon:.2f}")

    # Horário da cidade desejada
    tf = TimezoneFinder()
    timezone = tf.timezone_at(lat=lat, lng=lon)
    if timezone:
        tz = pytz.timezone(timezone)
    else:
        cidade_lower = cidade.lower()
        fuso = fuso_por_cidade.get(cidade_lower, 'America/Sao_Paulo')
        tz = pytz.timezone(fuso)

    hora_local = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    print(f"🕐 Hora local: {hora_local}")

    # Clima
    api_key = "368ad6a5b8b26824f2025e96846f1324"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"

    print(f"Teste: lat={lat}, lon={lon}")

    response = requests.get(url)
    print(f"Status: {response.status_code}")
    print(f"Erro: {response.text[:150]}")

    data = response.json()

    print(f"TEMPERATURA: {data.get('main', {}).get('temp', 'N/A')}")

    if response.status_code == 200:
        temp = data["main"]["temp"]
        print(f"🌡️  Temperatura: {temp}°C")
    else:
        print("❌ Erro na API!")