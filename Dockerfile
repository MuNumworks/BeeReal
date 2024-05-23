# Utiliser une image de base Python 3.10.14
FROM python:3.10.14-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements.txt et main.py dans le conteneur
COPY requirements.txt requirements.txt
COPY main.py main.py

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Définir la variable d'environnement pour le jeton du bot
ENV DISCORD_TOKEN=${DISCORD_TOKEN}

# Commande pour exécuter le bot
CMD ["python", "main.py"]
