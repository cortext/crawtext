# Installation

* Apercu des briques logicielles
* Installer MongoDB
* Mise en place d'un virtualenv
* Installation du parser LXML
* Installation des dépendances du projet

## Apercu des briques logicielles

Crawtext fonctionne en Python 2.7 avec une base de données Mongo 3.2

4 étapes d'installation:
* installation de la base de données en Backend : 

    MongoDB [cf. mes reflexions](#choix-dimplémentation-et-retour-sur-expérience)

* installation du parser lxml:

    On peut rencontrer certains problèmes à l'installation du package python ```lxml```
    que nous contournons ici

* cloner le repository de crawtext

* création d'un environnement virtuel et installation des packages supplémentaire

    Il est recommandé d'isoler l'installation de Crawtext dans un ```virtualenv```
    et profiter du système d'installation simplifiée avec ```pip```


## Installer MongoDB

Mongo doit être installé en dehors de l'environnement 
* On LINUX (Debian based distribution):

    Packages are compatibles with:
        * Debian 7 Wheezy (and older)
        * Ubuntu 12.04 LTS and 14.04 LTS (and older)
    ``` 
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
    echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org=3.2.1 mongodb-org-server=3.2.1 mongodb-org-shell=3.2.1 mongodb-org-mongos=3.2.1 mongodb-org-tools=3.2.1
    ``` 
* On MAC OS/X: 
(from LionX to newest)

``` 
brew update
brew install mongodb --with-openssl
```

* On Windows:
    refer to [official MongoDB installation procedure](https://docs.mongodb.org/manual/tutorial/install-mongodb-on-windows/)

Maintenant vérifier que MongoDB  est bien installé:

```
$ mongo
MongoDB shell version: 3.2.0
connecting to: test
>
```
Type Ctrl+C to quit
    
    
### Activer le virtualenv

Verifier que virtualenv est bien installé

```
$ virtualenv --version
```

If you got a “Command not found” when you tried to use virtualenv, try:
```
$ sudo pip install virtualenv
```
or
``` 
sudo apt-get install python-virtualenv # for a Debian-based system
```

```
$ virtualenv cortext-box
$ cd cortext-box
$ source bin/activate
```

(source bin/deactivate pour sortir)

### Installer LXML

Install LXML may cause some troubelshooting: to avoid it install 
additionnal packages

* On Debian
```
sudo apt-get install libxml2-dev libxslt-dev python-dev
```
* On MAC

```
brew install libxml2
brew install libxslt
brew link libxml2 --force
brew link libxslt --force
```
* On windows

Select the source file that corresponds to you architecture (32 or 64 bits)
open an run it
[lxml ditributions | http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml]

### Clone the repository

```
$ git clone https://github.com/cortext/crawtext
$ cd crawtext
```

Install additional packages using the requirements file

``` 
$ pip install -r requirements.pip

``` 




