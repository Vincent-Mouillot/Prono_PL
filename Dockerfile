FROM rocker/shiny:latest

# Créer un utilisateur non-root (par exemple 'shinyuser') et un répertoire pour l'application
RUN useradd -m shinyuser

# Installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de l'application dans le conteneur
COPY ./app /srv/shiny-server/

# Changer les permissions pour l'utilisateur shinyuser
RUN chown -R shinyuser:shinyuser /srv/shiny-server

# Passer à l'utilisateur non-root
USER shinyuser

# Exposer le port 3838
EXPOSE 3838

# Lancer Shiny Server
CMD ["/usr/bin/shiny-server"]
