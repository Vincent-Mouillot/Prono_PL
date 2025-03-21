FROM rocker/shiny:latest

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de l'application dans le répertoire de Shiny Server
COPY ./app /srv/shiny-server/

# Donner les permissions appropriées à l'utilisateur shiny (par défaut dans le conteneur Docker)
RUN chown -R shiny:shiny /srv/shiny-server

# Exposer le port
EXPOSE 3838

# Lancer Shiny Server
CMD ["/usr/bin/shiny-server"]