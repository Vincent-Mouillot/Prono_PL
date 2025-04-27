# Utiliser une image de base Shiny
FROM rocker/shiny:latest

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier le fichier DESCRIPTION pour gérer les dépendances R
COPY DESCRIPTION /DESCRIPTION

# Installer les dépendances R listées dans DESCRIPTION
RUN R -e "install.packages('remotes'); remotes::install_deps(dependencies=TRUE)"

# Copier tout le projet (y compris les fichiers, dossiers, etc.) dans /srv/shiny-server/
COPY ./ /srv/shiny-server/

# Donner les permissions appropriées à l'utilisateur shiny
RUN chown -R shiny:shiny /srv/shiny-server

# Exposer le port de Shiny Server
EXPOSE 3838

# Lancer Shiny Server
CMD ["/usr/bin/shiny-server"]
