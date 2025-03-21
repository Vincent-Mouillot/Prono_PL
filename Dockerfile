 FROM rocker/shiny:latest

# Installer les dépendances
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier l'application Shiny
COPY . /srv/shiny-server/

# Définir les permissions
RUN chown -R shiny:shiny /srv/shiny-server

# Exposer le port 3838
EXPOSE 3838

# Lancer Shiny Server
CMD ["/usr/bin/shiny-server"]