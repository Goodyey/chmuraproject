import os
import datetime
import logging
import socket
import requests
from flask import Flask, render_template, request, jsonify

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

AUTHOR_NAME = "Łukasz"
AUTHOR_SURNAME = "Kabala"

PORT = int(os.environ.get("PORT", 5000))

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")  # Pobieranie klucza z zmiennej środowiskowej

# Predefiniowana lista krajów i miast
COUNTRIES_AND_CITIES = {
    "Polska": ["Warszawa", "Kraków", "Gdańsk", "Poznań", "Wrocław"],
    "Niemcy": ["Berlin", "Hamburg", "Monachium", "Kolonia", "Frankfurt"],
    "Francja": ["Paryż", "Marsylia", "Lyon", "Tuluza", "Nicea"],
    "Włochy": ["Rzym", "Mediolan", "Neapol", "Turyn", "Florencja"],
    "Hiszpania": ["Madryt", "Barcelona", "Walencja", "Sewilla", "Malaga"]
}

@app.route('/')
def index():
    """Strona główna aplikacji z formularzem wyboru kraju i miasta."""
    return render_template('index.html', countries=COUNTRIES_AND_CITIES)

@app.route('/get_cities', methods=['POST'])
def get_cities():
    """Endpoint zwracający miasta dla wybranego kraju."""
    country = request.json['country']
    cities = COUNTRIES_AND_CITIES.get(country, [])
    return jsonify(cities)

@app.route('/weather', methods=['POST'])
def weather():
    """Endpoint zwracający dane pogodowe dla wybranej lokalizacji."""
    city = request.form.get('city')
    country = request.form.get('country')
    
    if not city or not country:
        return jsonify({"error": "Nie wybrano miasta lub kraju"}), 400
    
    # Pobieranie danych pogodowych z OpenWeatherMap
    try:
        weather_data = get_weather_data(city)
        logger.info(f"Pomyślnie pobrano dane pogodowe dla: {city}, {country}")
        return render_template('weather.html', weather=weather_data, city=city, country=country)
    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych pogodowych: {str(e)}")

        error_message = "Nie udało się pobrać danych pogodowych. "
        if "Nieprawidłowy klucz API" in str(e):
            error_message += "Problem z autoryzacją do API pogodowego."
        elif "Nieprawidłowy format danych" in str(e):
            error_message += "Otrzymano nieprawidłowe dane z serwisu pogodowego."
        else:
            error_message += "Prosimy spróbować ponownie później."
            
        return render_template('error.html', error=error_message, city=city, country=country), 500

def get_weather_data(city):
    """Funkcja pobierająca dane pogodowe z API OpenWeatherMap."""
    if not API_KEY:
        logger.error("Brak klucza API OpenWeatherMap")
        raise ValueError("Brak klucza API OpenWeatherMap. Ustaw zmienną środowiskową OPENWEATHER_API_KEY.")
        
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=pl"
    logger.info(f"Wysyłanie zapytania do API OpenWeatherMap dla miasta: {city}")
    response = requests.get(url)
    
    # Obsługa błędów dla złych odpowiedzi API
    if response.status_code == 401:
        logger.error(f"Błąd autoryzacji API (401). Sprawdź poprawność klucza API: {API_KEY[:5]}...")
        raise ValueError("Nieprawidłowy klucz API OpenWeatherMap")
    elif response.status_code != 200:
        logger.error(f"Błąd API ({response.status_code}): {response.text}")
        response.raise_for_status()
        
    data = response.json()
    
    # Sprawdzanie poprawności danych z API
    try:
        temperature = float(data["main"]["temp"]) if "temp" in data["main"] else 0.0
        feels_like = float(data["main"]["feels_like"]) if "feels_like" in data["main"] else 0.0
        humidity = int(data["main"]["humidity"]) if "humidity" in data["main"] else 0
        pressure = int(data["main"]["pressure"]) if "pressure" in data["main"] else 0
        wind_speed = float(data["wind"]["speed"]) if "wind" in data and "speed" in data["wind"] else 0.0
        
        weather_description = data["weather"][0]["description"] if data.get("weather") and len(data["weather"]) > 0 and "description" in data["weather"][0] else "Brak danych"
        weather_icon = data["weather"][0]["icon"] if data.get("weather") and len(data["weather"]) > 0 and "icon" in data["weather"][0] else "01d"
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Błąd przetwarzania danych pogodowych: {str(e)}")
        logger.error(f"Otrzymane dane: {data}")
        raise ValueError(f"Nieprawidłowy format danych z API: {str(e)}")
    
    # Przetwarzanie danych pogodowych z zapewnieniem prawidłowych typów
    weather = {
        "description": weather_description,
        "temperature": temperature,
        "feels_like": feels_like,
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "icon": weather_icon
    }
    
    return weather

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local_ip = get_local_ip()
    
    logger.info(f"===============================================")
    logger.info(f"Data uruchomienia: {start_time}")
    logger.info(f"Autor: {AUTHOR_NAME} {AUTHOR_SURNAME}")
    logger.info(f"Aplikacja nasłuchuje na: {local_ip}:{PORT}")
    logger.info(f"===============================================")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)