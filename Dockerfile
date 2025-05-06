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




