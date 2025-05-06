# Chmura Project

## Autor: Łukasz Kabala

Repozytorium zawiera aplikację webową napisaną w języku Python z wykorzystaniem frameworka Flask, która umożliwia sprawdzanie aktualnych warunków pogodowych dla wybranych miast. Aplikacja jest opakowana w kontener Docker z wykorzystaniem najlepszych praktyk konteneryzacji.

## 1. Opis aplikacji

### Funkcjonalność

Aplikacja realizuje następujące funkcjonalności:

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

Poniższy plik Dockerfile został opracowany z uwzględnieniem najlepszych praktyk:
- Wieloetapowe budowanie obrazu (multi-stage build)
- Optymalizacja pod kątem cache'a i ilości warstw
- Uruchamianie aplikacji jako użytkownik bez uprawnień roota
- Implementacja mechanizmu HEALTHCHECK
- Zgodność ze standardem OCI (Open Container Initiative) dotyczącym metadanych

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

#### Wypchnięcie obrazu do Docker Hub
```bash
# Najpierw zalogowanie
docker login

# Oznaczenie obrazu z nazwą użytkownika
docker tag aplikacja-pogodowa:latest kazuhiram/aplikacja-pogodowa:latest

# Wypchnięcie do Docker Hub
docker push kazuhiram/aplikacja-pogodowa:latest
```

## Linki

- Repozytorium GitHub: [https://github.com/username/aplikacja-pogodowa](https://github.com/username/aplikacja-pogodowa)
- Docker Hub: [https://hub.docker.com/r/username/aplikacja-pogodowa](https://hub.docker.com/r/username/aplikacja-pogodowa)

## Dodatkowe informacje

### Analiza warstw obrazu Docker

Zbudowany obraz składa się z mniejszej liczby warstw niż tradycyjny Dockerfile dzięki:
1. Połączeniu powiązanych poleceń (np. wiele ENV w jednej linii)
2. Wieloetapowemu budowaniu, które eliminuje warstwy narzędzi budujących
3. Skopiowaniu tylko niezbędnych plików do obrazu finalnego

### Uzasadnienie zastosowanych technik

1. **Wieloetapowe budowanie** - pozwala na zmniejszenie rozmiaru finalnego obrazu poprzez eliminację narzędzi budujących i plików pośrednich.

2. **Optymalizacja pod kątem cache'a** - umieszczenie rzadko zmieniających się elementów (np. instalacji zależności) wcześniej w Dockerfile, a często zmieniających się (np. kodu aplikacji) później, co przyspiesza budowanie obrazu.

3. **Ograniczenie liczby warstw** - łączenie podobnych instrukcji w jednym poleceniu RUN/ENV, co zmniejsza rozmiar obrazu i przyspiesza jego załadowanie.

4. **Uruchamianie jako nieprivilegowany użytkownik** - zwiększa bezpieczeństwo kontenera poprzez ograniczenie potencjalnych szkód w przypadku naruszenia bezpieczeństwa.

5. **Healthcheck** - umożliwia automatyczne wykrywanie problemów z aplikacją i podejmowanie działań naprawczych (np. restart kontenera).

### Porównanie z alternatywnymi podejściami

1. **Obraz bazowy Alpine vs Slim**:
   - Wybrano `python:3.10-slim` zamiast `python:3.10-alpine` ze względu na lepszą kompatybilność i wydajność bibliotek Pythona
   - Obraz alpine byłby mniejszy, ale mógłby wymagać dodatkowych zależności systemowych

2. **Scratch vs Distroless vs Slim**:
   - Warstwa `scratch` nie została wykorzystana, ponieważ aplikacja Pythona wymaga środowiska uruchomieniowego
   - Obrazy `distroless` byłyby bardziej minimalistyczne, ale trudniejsze w debugowaniu

## 5. Obsługa wielu architektur w procesie budowania obrazu

### Budowanie obrazów dla wielu architektur z wykorzystaniem cache

Poniżej przedstawiam rozwiązanie do zadania polegającego na zbudowaniu obrazów kontenera na architektury linux/arm64 oraz linux/amd64 z wykorzystaniem zaawansowanych funkcji buildx.

#### Przygotowanie środowiska

1. Upewnij się, że masz zainstalowany Docker z obsługą buildx:

```bash
docker buildx version
```

2. Utwórz i użyj nowy builder dockercontainer:

```bash
# Utwórz nowy builder
docker buildx create --name multiarch-builder --driver docker-container --use

# Sprawdź status
docker buildx inspect multiarch-builder --bootstrap
```

#### Przygotowanie do pobierania kodu z repozytorium GitHub

1. Wygeneruj parę kluczy SSH (jeśli jeszcze nie masz):

```bash
ssh-keygen -t ed25519 -C "email@example.com"
```

2. Dodaj klucz publiczny do swojego konta GitHub w ustawieniach SSH keys.

3. Utwórz agent SSH i dodaj klucz prywatny:

```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```

#### Konfiguracja cache z backend registry

1. Zaloguj się do Docker Hub:

```bash
docker login
```

2. Utwórz plik `buildx-config.toml` z konfiguracją cache:

```toml
[registry."docker.io/username"]
  token = "TWÓJ_TOKEN_DOCKER_HUB"
```

#### Budowanie obrazu wieloarchitekturowego

Wykonaj poniższe polecenie, aby zbudować obraz dla wielu architektur z wykorzystaniem cache i pobieraniem kodu bezpośrednio z GitHub:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --push \
  --ssh default \
  --cache-from=type=registry,ref=username/aplikacja-pogodowa-cache \
  --cache-to=type=registry,ref=username/aplikacja-pogodowa-cache,mode=max \
  --build-arg SSH_PRIVATE_KEY="$(cat ~/.ssh/id_ed25519)" \
  -f Dockerfile.multiarch \
  -t username/aplikacja-pogodowa:multiarch \
  https://github.com/username/aplikacja-pogodowa.git
```

#### Plik Dockerfile.multiarch

Poniżej jest zawartość pliku `Dockerfile.multiarch` wykorzystującego funkcjonalność `mount ssh` do pobierania kodu bezpośrednio z repozytorium GitHub:

```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.10-slim AS builder

# Informacja o autorze (standard OCI)
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

# Pobieranie kodu bezpośrednio z GitHub z użyciem SSH
RUN --mount=type=ssh \
    mkdir -p ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts && \
    git clone git@github.com:username/aplikacja-pogodowa.git . && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

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
    # Ustawienie pustego klucza API - powinien być dostarczany przy uruchomieniu
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

# Kopiujemy kod aplikacji i szablony z etapu budowania
COPY --from=builder --chown=appuser:appuser /build/app.py .
COPY --from=builder --chown=appuser:appuser /build/templates/ templates/

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

#### Weryfikacja manifestu obrazu

Po zbudowaniu i wypchnięciu obrazu, sprawdź manifest, aby potwierdzić obsługę obu architektur:

```bash
docker buildx imagetools inspect username/aplikacja-pogodowa:multiarch
```

Wynik powinien zawierać informacje o obrazach dla obu platform (linux/amd64 i linux/arm64):

```
Name:      docker.io/username/aplikacja-pogodowa:multiarch
MediaType: application/vnd.docker.distribution.manifest.list.v2+json
Digest:    sha256:...

Manifests:
  Name:      docker.io/username/aplikacja-pogodowa:multiarch@sha256:...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/amd64

  Name:      docker.io/username/aplikacja-pogodowa:multiarch@sha256:...
  MediaType: application/vnd.docker.distribution.manifest.v2+json
  Platform:  linux/arm64
```

#### Sprawdzenie obrazu cache

Sprawdź, czy obraz z danymi cache został poprawnie utworzony:

```bash
docker buildx imagetools inspect username/aplikacja-pogodowa-cache
```

#### Testowanie obrazu na różnych platformach

Dla testowania na architekturze amd64:
```bash
docker run --platform linux/amd64 -p 5000:5000 -e OPENWEATHER_API_KEY="twój_klucz_api" username/aplikacja-pogodowa:multiarch
```

Dla testowania na architekturze arm64 (jeśli dostępna):
```bash
docker run --platform linux/arm64 -p 5000:5000 -e OPENWEATHER_API_KEY="twój_klucz_api" username/aplikacja-pogodowa:multiarch
```

### Wnioski

Zastosowanie rozszerzonego frontendu Dockerfile oraz sterownika buildx dockercontainer pozwoliło na:

1. Bezpośrednie pobieranie kodu aplikacji z repozytorium GitHub
2. Budowanie obrazów dla wielu architektur (linux/amd64, linux/arm64)
3. Efektywne wykorzystanie pamięci podręcznej (cache) w trybie max
4. Automatyczne publikowanie obrazów w rejestrze Docker Hub

Takie podejście znacząco przyspiesza proces CI/CD, umożliwiając łatwe aktualizacje obrazu kontenera po zmianach w repozytorium kodu.