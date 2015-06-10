#Python2.7 official version based on Debian Jessie
# See https://github.com/docker-library/python/blob/526ee08b34a8cd403ff47cc03001f8025738e70e/2.7/Dockerfile
FROM       python:2.7
MAINTAINER c24b <4barbes@gmail.com>

#Creation d'un dossier pour les exports et rapports
RUN mkdir /scripts
RUN mkdir -p /crawtext/projects

#Le rendre accessible depuis l'extérieur
VOLUME ["/crawtext/projects/"]



#Copier les scripts à l'intérieur du container
COPY /install /install
COPY /scripts /scripts

#Installer les dépendances (Python Pip déjà installé avexc python2.7)
RUN pip install --upgrade pip
RUN pip install -r /install/requirements.pip 

CMD ["/bin/bash"]




