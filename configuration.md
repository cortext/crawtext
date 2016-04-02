# Configuration

Crawtext se configure à deux niveaux:
* Environnement
* Projet

## Environnement par défaut

Crawtext propose un fichier de configuration par défaut: ```config/settings.json```

Ce fichier définit l'environnement de fonctionnement du crawler:
* l'utilisateur du crawler: c'est dans un dossier à son nom que se trouveront tous les crawls et leur résultats 
* la base de données en back-end qui gère les paramêtres des crawls et leur récurrence
* l'environnement dans lequel seront stockés tous les dossiers de tous les utilisateurs
* l'url où sont exposés l'avancement du crawl et ses paramêtres(TO DO)

Le fichier disponible [ici](./config/settings.json) se présente sous cette forme
```
{
	"user":{
        "username": "user@cortext.net",
        "password": "keepitsecret"
        },
	"db": {
        "provider": "mongo",
		"host": "localhost",
		"port": 27017,
        "password": "",
        "db_name": "demo_crawtext",
		"collection": "projects"
	},
    "env": {
        "directory": "",
        "name": "crawtext"
        },
    "website":{
        "host": "localhost",
        "port": 8080
    }
}
```
Il suffit d'en modifier les valeurs et Crawtext met à jour la configuration et le paramêtrage à chaque lancement d'un crawl.
Il est recommandé pour les débutants de ne changer que le **username**

Voir le [fichier de configuration](./config/settings.json)

## Paramétrage d'un projet

La création ou mise à jour d'un projet se fait via un fichier au format json de parametrages du projet
Un example de parametrage est donné dans ```config/example.json```
Il suffit de modifier les valeurs, et de choisir un nom pour définir son projet. Pour activer désactiver des filtres il suffit de mettre la valeur à vrai ou faux en modifiant le fichier par [ici](/config/example.json)

```
{
    #definir le nom du projet de crawl
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
            "key": "APIKeyGivenByBing",
            "nb": 100
            }
        }
}
```