# CRAWTEXT (FR)

For [ENGLISH VERSION](./README_EN.md) click [here](./README_EN.md)

Crawtext est un [**crawler**](https://fr.wikipedia.org/wiki/Robot_d'indexation) 
ou un robot d'indexation de texte issus de page web en mode console
qui permet la constitution de gros corpus web textuels
autour d'une expression de recherche donnée.

La capitalisation de données web se paramêtre sur une fréquence:
 * journalière
 * hebdomadaire 
 * mensuelle 

Crawtext est un crawler web ciblée. 

Il stocke dans une base de données les pages web qui correspondent à l'expression de recherche demandée.

Il existe plusieurs stratégies de crawl paramétrable par l'utilisateur:
* crawl d'un sujet/thématique exprimée à travers une expression de recherche
* crawl d'un site web complet
* crawl mixte sur un ou plusieurs sites web sources d'un sujet ou thématique 
exprimée à travers une expression de recherche

Le crawl nécessite un point de départ pour démarrer son parcours appelés ```seeds```
Plusieurs méthodes sont proposées qui peuvent être mixés en ajoutant:
* une url simple
* un fichier contenant une url par ligne
* une clé d'API au moteur de recherche **BING**: 
    * on peut l'obtenir en s'inscrivant [ici](https://datamarket.azure.com/dataset/5BA839F1-12CE-4CCE-BF57-A49D98D29A44)
    * une expression de recherche est alors indispensable au fonctionnement du crawl
        
Plusieurs filtres additionnels sont proposés:

* un filtre de langue: le crawler selectionnera uniquement les textes qui correspondent à la langue selectionnée
    * Ce filtre suit la norme [ISO 639-1](https://fr.wikipedia.org/wiki/Liste_des_codes_ISO_639-1)
* un filtre de profondeur de crawl: le crawler arretera la recherche quand le nombre d'étape sera atteint.
    * Ce filtre permet de réduire les temps de traitement souvent très long.
* un filtre de requête: le crawler selectionnera uniquement les textes qui correspondent à cette expression de recherche.
    * Ce filtre est indispensable dans le cas d'un crawl autour d'un sujet ou d'une thématique
        

## Installation

### Apercu des briques logicielles
4 étapes d'installation:
- installation de la base de données en Backend : 

MongoDB [cf. mes reflexions](#choix-dimplémentation-et-retour-sur-expérience)

- installation du parser lxml:

On peut rencontrer certains problèmes à l'installation du package python ```lxml```
que nous contournons ici

- cloner le repository de crawtext

- création d'un environnement virtuel et installation des packages supplémentaire

Il est recommander d'isoler l'installation de Crawtext dans un ```virtualenv```
et profiter du système d'installation simplifiée avec ```pip```

### Installer MongoDB

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
    refer to [official MongoDB installation procedure] [https://docs.mongodb.org/manual/tutorial/install-mongodb-on-windows/]

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

Maintenant que nous sommes dans le virtualenv
lxml distribution for python requière quelques packets additionnel

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

### Cloner le repository

```
$ git clone https://github.com/cortext/crawtext
$ cd crawtext
```

Installer les packets additionnels

``` 
$ pip install -r requirements.pip

``` 

## Configuration
### Configuration par défaut:

Crawtext offre un environnement de fonctionnement par défaut:
stocké dans le fichier ```settings.json```
- une base de données de taches qui liste toutes les projets 
- un environnement par défault pour le fonctionnementdu crawler
- un dossier d'utilisateur qui contient un dossier pour chaque projet qui contient les résultats des crawls
- une url par défaut pour exposer les résultats sur le web

    Voir le (fichier de configuration) [./config/settings.json]

### Paramêtrages d'un projet:
Le paramêtrage d'un projet se fait par création ou modification du fichier ```example.json```
```javascript:
{
    #definir le nom du projet
    "name": "COP21",
    #activer les filtres en mettant "active":true 
    "filters": {
        #profondeur maximale
        "depth":{ 
            "active": true,
            "depth": 5
            },
        #filtre de langue
        "lang":{
            "active": false,
            
            "lang": "en"
            },
        # expression de recherche
        "query":{
            "active": false,
            "query": "(COP 21) OR (COP21)"
            }
    },
    #fréquence du crawl
    "scheduler": {
        "active": true,
        "days": 7
    },
    #point de départ du crawl (seeds)
    "seeds": {
        "url":{
            "active": false,
            "url": "http://www.lefigaro.fr"
            },
        "file":{
            "active": false,
            "file": "./config/sources.txt"
            },
        "search": {
            "active": true,
            "key": "J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o",
            "nb": 100
            }
        }
}
```

## Utilisation des résultats

## Etat de l'art

## Choix d'implémentation et retour sur expérience

