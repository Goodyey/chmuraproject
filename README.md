# Chmura project

Aplikacja webowa umożliwiająca sprawdzenie aktualnej pogody dla wybranych miast w różnych krajach.

## Funkcjonalności

1. Po uruchomieniu kontenera, aplikacja zapisuje w logach:
   - Datę uruchomienia
   - Imię i nazwisko autora
   - Port TCP, na którym nasłuchuje

2. Umożliwia wybór kraju i miasta z predefiniowanej listy
3. Wyświetla aktualne dane pogodowe dla wybranej lokalizacji:
   - Temperatura aktualna i odczuwalna
   - Opis pogody i ikona
   - Wilgotność
   - Ciśnienie
   - Prędkość wiatru

## Wymagania

- Docker
- Klucz API do OpenWeatherMap (darmowy)

## Struktura projektu

```
chmuraprojects/
├── app.py                 # Główny plik aplikacji
├── Dockerfile             # Konfiguracja kontenera
├── requirements.txt       # Zależności Python
└── templates/             # Szablony HTML
    ├── index.html         # Strona główna
    ├── weather.html       # Strona z danymi pogodowymi
    └── error.html         # Strona błędów
```

## Instrukcja uruchomienia

### 1. Uzyskaj klucz API OpenWeatherMap

Zarejestruj się na stronie [OpenWeatherMap](https://openweathermap.org/api) i uzyskaj darmowy klucz API.

### 2. Ustaw klucz API jako zmienną środowiskową

Masz dwie opcje:

1. Edytuj plik Dockerfile i zmień wartość zmiennej `OPENWEATHER_API_KEY` na swój klucz API:

```dockerfile
ENV OPENWEATHER_API_KEY="twój_klucz_api_openweathermap"
```

2. Lub przekaż klucz podczas uruchamiania kontenera:

```bash
docker run -p 5000:5000 -e OPENWEATHER_API_KEY="twój_klucz_api_openweathermap" chmuraproject
```

### 3. Zbuduj i uruchom kontener Docker

```bash
# Zbuduj obraz
docker build -t chmuraproject .

# Uruchom kontener
docker run -p 5000:5000 chmuraproject
```

### 4. Korzystanie z aplikacji

Otwórz przeglądarkę i przejdź pod adres:

```
http://localhost:5000
```

## Struktura katalogów dla szablonów

Przed uruchomieniem aplikacji należy utworzyć katalog `templates` i umieścić w nim pliki HTML:

```bash
mkdir templates
# Skopiuj pliki index.html i weather.html do katalogu templates
```

## Autor

Łukasz Kabala