# Chmura Project

## Autor: Łukasz Kabala

## 1. Opis aplikacji

Aplikacja realizuje zakres podstawowy zadania 1:

a. Po uruchomieniu kontenera, aplikacja zapisuje w logach:
   - Datę uruchomienia
   - Imię i nazwisko autora
   - Port TCP, na którym aplikacja nasłuchuje

b. Aplikacja pozwala na wybór kraju i miasta z predefiniowanej listy oraz zatwierdzenie tego wyboru, po czym wyświetla aktualną pogodę w wybranej lokalizacji.

### Kod źródłowy

#### app.py

```python
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

# Dane autora
AUTHOR_NAME = "Łukasz"
AUTHOR_SURNAME = "Kabala"

# Port nasłuchiwania - domyślnie 5000, ale możliwy do zmiany przez zmienną środowiskową
PORT = int(os.environ.get("PORT", 5000))

# Klucz API do OpenWeatherMap - pobierany z zmiennej środowiskowej
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
        # Zwróć bardziej czytelny błąd dla użytkownika końcowego
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
    
    # Bardziej szczegółowa obsługa błędów
    if response.status_code == 401:
        logger.error(f"Błąd autoryzacji API (401). Sprawdź poprawność klucza API: {API_KEY[:5]}...")
        raise ValueError("Nieprawidłowy klucz API OpenWeatherMap")
    elif response.status_code != 200:
        logger.error(f"Błąd API ({response.status_code}): {response.text}")
        response.raise_for_status()
        
    data = response.json()
    
    # Sprawdzanie i konwersja typów danych, aby upewnić się, że wartości numeryczne są faktycznie liczbami
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
    """Endpoint sprawdzający stan aplikacji."""
    return jsonify({"status": "ok"})

def get_local_ip():
    """Funkcja zwracająca lokalny adres IP."""
    try:
        # Tworzenie tymczasowego socketu, aby uzyskać adres IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"  # Fallback do localhost

if __name__ == "__main__":
    # Logowanie informacji o uruchomieniu
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    local_ip = get_local_ip()
    
    logger.info(f"===============================================")
    logger.info(f"Data uruchomienia: {start_time}")
    logger.info(f"Autor: {AUTHOR_NAME} {AUTHOR_SURNAME}")
    logger.info(f"Aplikacja nasłuchuje na: {local_ip}:{PORT}")
    logger.info(f"===============================================")
    
    # Uruchomienie serwera Flask
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

#### Szablony HTML (templates/)

**index.html**
```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aplikacja Pogodowa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            padding-top: 50px;
        }
        .container {
            max-width: 600px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .form-select {
            margin-bottom: 15px;
        }
        .btn-primary {
            width: 100%;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Aplikacja Pogodowa</h1>
            <p>Wybierz kraj i miasto, aby sprawdzić aktualną pogodę</p>
        </div>
        
        <form action="/weather" method="post">
            <div class="mb-3">
                <label for="country" class="form-label">Kraj</label>
                <select id="country" name="country" class="form-select" required>
                    <option value="" selected disabled>Wybierz kraj</option>
                    {% for country in countries %}
                    <option value="{{ country }}">{{ country }}</option>
                    {% endfor %}
                </select>
            </div>
            
            <div class="mb-3">
                <label for="city" class="form-label">Miasto</label>
                <select id="city" name="city" class="form-select" required disabled>
                    <option value="" selected disabled>Najpierw wybierz kraj</option>
                </select>
            </div>
            
            <button type="submit" class="btn btn-primary">Sprawdź pogodę</button>
        </form>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('country').addEventListener('change', function() {
            const country = this.value;
            const citySelect = document.getElementById('city');
            
            // Wyczyść listę miast
            citySelect.innerHTML = '<option value="" selected disabled>Wybierz miasto</option>';
            citySelect.disabled = true;
            
            if (country) {
                // Wykonaj zapytanie AJAX, aby pobrać miasta dla wybranego kraju
                fetch('/get_cities', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ country: country }),
                })
                .then(response => response.json())
                .then(cities => {
                    // Dodaj miasta do listy rozwijanej
                    cities.forEach(city => {
                        const option = document.createElement('option');
                        option.value = city;
                        option.textContent = city;
                        citySelect.appendChild(option);
                    });
                    
                    // Odblokuj listę miast
                    citySelect.disabled = false;
                })
                .catch(error => {
                    console.error('Błąd:', error);
                });
            }
        });
    </script>
</body>
</html>
```

**weather.html**
```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pogoda - {{ city }}, {{ country }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            padding-top: 50px;
        }
        .container {
            max-width: 600px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .weather-icon {
            width: 100px;
            height: 100px;
            margin: 0 auto;
            display: block;
        }
        .weather-main {
            text-align: center;
            margin-bottom: 30px;
        }
        .weather-details {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .weather-detail {
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
        }
        .btn-back {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Aktualna pogoda</h1>
            <h2>{{ city }}, {{ country }}</h2>
        </div>
        
        <div class="weather-main">
            <img src="http://openweathermap.org/img/wn/{{ weather.icon }}@2x.png" alt="Ikona pogody" class="weather-icon">
            <h3>{{ weather.description|capitalize }}</h3>
            <h1>{{ "%.1f"|format(weather.temperature) }}°C</h1>
            <p>Odczuwalna: {{ "%.1f"|format(weather.feels_like) }}°C</p>
        </div>
        
        <div class="weather-details">
            <div class="weather-detail">
                <span>Wilgotność:</span>
                <strong>{{ weather.humidity }}%</strong>
            </div>
            <div class="weather-detail">
                <span>Ciśnienie:</span>
                <strong>{{ weather.pressure }} hPa</strong>
            </div>
            <div class="weather-detail">
                <span>Prędkość wiatru:</span>
                <strong>{{ weather.wind_speed }} m/s</strong>
            </div>
        </div>
        
        <a href="/" class="btn btn-primary btn-back">Powrót do strony głównej</a>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

**error.html**
```html
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Błąd - Aplikacja Pogodowa</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f5f5f5;
            padding-top: 50px;
        }
        .container {
            max-width: 600px;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .error-container {
            background-color: #f8d7da;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            color: #721c24;
        }
        .btn-back {
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Wystąpił błąd</h1>
            <h2>{{ city }}, {{ country }}</h2>
        </div>
        
        <div class="error-container">
            <h3>Nie udało się pobrać danych pogodowych</h3>
            <p>{{ error }}</p>
        </div>
        
        <a href="/" class="btn btn-primary btn-back">Powrót do strony głównej</a>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

#### requirements.txt
```
Flask==2.2.3
requests==2.28.2
Werkzeug==2.2.3
```

## 2. Plik Dockerfile

```dockerfile
# Etap 1: Budowanie zależności
FROM python:3.10-slim AS builder

# Informacja o mnie zgodnie ze standardem OCI
LABEL org.opencontainers.image.authors="Łukasz Kabala"
LABEL org.opencontainers.image.title="Aplikacja Pogodowa"
LABEL org.opencontainers.image.description="Kontener z aplikacją pogodową wyświetlającą dane pogodowe dla wybranych miast"
LABEL org.opencontainers.image.version="1.0.0"

# Ustawiamy zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Ustawienie katalogu roboczego
WORKDIR /build

# Kopiujemy tylko plik wymagań, aby wykorzystać cache warstw Dockera
COPY requirements.txt .

# Instalujemy zależności do oddzielnego katalogu
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Etap 2: Obraz finalny
FROM python:3.10-slim

# Kopiujemy metadane z etapu budowania
LABEL org.opencontainers.image.authors="Łukasz Kabala"
LABEL org.opencontainers.image.title="Aplikacja Pogodowa"
LABEL org.opencontainers.image.description="Kontener z aplikacją pogodową wyświetlającą dane pogodowe dla wybranych miast"
LABEL org.opencontainers.image.version="1.0.0"

# Ustawiamy zmienne środowiskowe
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    # Ustawienie pustego klucza API - powinien być dostarczany przy uruchomieniu kontenera
    OPENWEATHER_API_KEY=""

# Kopiujemy zainstalowane zależności z etapu budowania
COPY --from=builder /install /usr/local

# Tworzymy użytkownika bez uprawnień roota dla bezpieczeństwa
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin -c "Docker image user" appuser && \
    mkdir -p /app/templates && \
    chown -R appuser:appuser /app

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiujemy kod aplikacji i szablony
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser templates/ templates/

# Eksponujemy port
EXPOSE $PORT

# Przełączamy się na użytkownika bez uprawnień roota
USER appuser

# Dodajemy healthcheck do sprawdzania stanu aplikacji
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Uruchamiamy aplikację
CMD ["python", "app.py"]
```

## 3. Polecenia do obsługi kontenera

### a. Zbudowanie obrazu kontenera

```bash
docker build -t aplikacja-pogodowa:latest .
```

Alternatywnie, aby oznaczyć obraz tagiem z wersją:

```bash
docker build -t aplikacja-pogodowa:1.0.0 .
```

### b. Uruchomienie kontenera

```bash
docker run -d -p 5000:5000 -e OPENWEATHER_API_KEY="twój_klucz_api" --name pogoda aplikacja-pogodowa
```

### c. Uzyskanie informacji wygenerowanych przez serwer podczas uruchamiania

```bash
docker logs pogoda
```

Aby śledzić logi na bieżąco:

```bash
docker logs -f pogoda
```

### d. Sprawdzenie liczby warstw obrazu

```bash
docker history aplikacja-pogodowa
```

Bardziej szczegółowa analiza warstw:

```bash
docker inspect aplikacja-pogodowa
```

### Dodatkowe przydatne polecenia

#### Sprawdzenie stanu kontenera
```bash
docker ps -a | grep pogoda
```

#### Zatrzymanie i usunięcie kontenera
```bash
docker stop pogoda
docker rm pogoda
```

## Linki

- Repozytorium GitHub: [https://github.com/Goodyey/chmuraproject]
- Docker Hub: [https://hub.docker.com/repository/docker/kazuhiram/aplikacja-pogodowa]