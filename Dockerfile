
# Utiliser une image Python officielle comme base
FROM python:3.11-slim-buster

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires dans le conteneur
COPY requirements.txt .
COPY bot.py .
COPY french_words.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port si nécessaire (pour les webhooks, mais ce bot utilise le polling)
# EXPOSE 80

# Commande pour lancer le bot
CMD ["python", "bot.py"]
