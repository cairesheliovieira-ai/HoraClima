import requests
from datetime import datetime
import pytz

# ========================================
print("🌍  BUSCADOR DE HORA E CLIMA MUNDIAL  🌍")
print("========================================")

#Pergunta a cidade desejada:
cidade = input("📍 Digite o nome da cidade: ").strip()
print(f"\n🔍 Pesquisando {cidade.title()}...\n")

print("Buscando coordenadas GPS...")
geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={cidade}&limit=1&appid=368ad6a5b8b26824f2025e96846f1324"
geo_resposta = requests.get(geo_url)
coordenadas = geo_resposta.json()

if coordenadas:
    latitude = coordenadas[0]['lat']
    longitude = coordenadas[0]['lon']
    pais = coordenadas[0]['country']

    print(f"✅ Coordenadas encontradas!")
    print(f"   📍 Latitude:  {latitude:.2f}")
    print(f"   📍 Longitude: {longitude:.2f}")
    print(f"   🏳️  País:      {pais}")

    print("🕐 Calculando hora local...")
    from timezonefinder import TimezoneFinder

    tf = TimezoneFinder()

    nome_fuso = tf.timezone_at(lat=latitude, lng=longitude)
    if nome_fuso:
        fuso_horario = pytz.timezone(nome_fuso)
        hora_local = datetime.now(fuso_horario).strftime("%H:%M")
        print(f"✅ Hora exata: {hora_local} ({nome_fuso.split('/')[-1]})")
    else:
        print("Calculando hora local...")
    tf = TimezoneFinder()
    fuso_nome = tf.timezone_at(lat=latitude, lng=longitude)
    if fuso_nome:
        tz = pytz.timezone(fuso_nome)
        hora = datetime.now(tz).strftime("%H:%M")
        print(f"🕐 {hora} ({fuso_nome.split('/')[-1]})")
    else:
        print("Hora 0 (fuso não disponível)")

    #Clima da cidade desejada
    print("\n🌤️ Buscando clima detalhado...")
    clima_url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid=368ad6a5b8b26824f2025e96846f1324&units=metric&lang=pt_br"
    dados_clima = requests.get(clima_url).json()

    if 'main' in dados_clima:
        temperatura = dados_clima['main']['temp']
        condicao = dados_clima['weather'][0]['description'].title()
        umidade = dados_clima['main']['humidity']

        print("\n Informações Completas:")
        print(f"🌡️  Temperatura: {temperatura}°C")
        print(f"☁️   Condição:    {condicao}")
        print(f"💧 Umidade:       {umidade}%")

    else:
        print("❌ Erro nos dados do clima!")

else:
    print("❌ Cidade não encontrada no banco de dados!")

print("\n" + "--" *70 )
resposta = input("🔄 Nova busca? (s/n): ")
if resposta.lower() == 's':
    print("\n" * 3)  #Limpa tela
    exec(open(__file__).read())  #Reinicia a busca de cidades
else:
    print("👋 Obrigado! Até logo!")