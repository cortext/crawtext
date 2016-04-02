# Tutoriel
## Crawl ciblé
Ici nous allons créer un crawl ciblé autour 
des prises de paroles en ligne sur la loi travail
Pour cela  nous allons créer le projet loi_travail
  ```name: "loi_travail"```
Pour un crawl ciblé autour d'une thématique nous avons besoin
d'une expression de recherche


Nous allons modifier dans la fichier la "query":
  ```
  "query":{
  
            "active": true, 
            "query": "loi AND (Travail OR El K?omri)" 
            }
  ```
Au vu du bruit médiatique autour de ce sujet nous allons limiter
la  profondeur du crawl à 3 soit le résultats des recherches + 2 niveaux
pour ne pas surcharger le crawler
 ```
 depth:{
         "active": true, 
         "depth":3
         },     
```
Le contenu qui nous intéresse est en français et on désire filtrer
 ```
 "lang":{
         "active": true, 
         "lang":"fr",
         },     
```

Le crawl doit partir d'une recherche initiale sur BING
nous allons modifier la partie seeds
* ajouter la clé d'API pour activer la recherche en ligne
* mettre le nombre de résultats que nous voulons récupérer (50)
* et désactiver les autres options en mettat à false

```
"seeds": {
        "url":{
            "active": false,
            "url": ""
            },
        "file":{
            "active": false,
            "file": ""
            },
        "search": {
            "active": true,
            "key": "J8zre1019v/dIT0oXXXXXXXXX",
            "nb": 50
            }
        }```

Le fichier final appelé loitravail.json prend donc cette forme:

```
{
    "name": "COP21",
    "filters": {
        "depth":{ 
            "active": true,
            "depth": 5
            },
        "lang":{
            "active": true,
            "lang": "en"
            },
        "query":{
            "active": true,
            "query": "(COP 21) OR (COP21)"
            }
    },
    "scheduler": {
        "active": true,
        "days": 7
    },
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
2. Lancer crawtext
3. Analyser les résultats

