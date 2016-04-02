# Tutoriel
## Crawl ciblé
Ici nous allons créer un crawl ciblé autour 
des prises de paroles en ligne sur la loi travail
Pour cela  nous allons créer le projet loitravail
en modifiant le fichier d'exemple dans name nous allons donc mettre 
LoiTravail
Dans query
Nous allons définir une requete
"Loi AND (travail OR El Khomri)"
Ajouter une clé d'API pour activer la recherche en ligne


    
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
3. 2. Lancer crawtext
3. Analyser les résultats

