# Basis-Image mit Python
FROM python:3.12

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Kopieren der requirements.txt
COPY requirements.txt .

# Installieren der Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren des gesamten Projektverzeichnisses in den Container
COPY . .

# Port freigeben
EXPOSE 5000

# Startbefehl für die Flask-App
CMD ["python", "-u", "app.py"]
