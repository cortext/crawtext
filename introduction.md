# Introduction

# Introduction

Crawtext est un [**crawler**](https://fr.wikipedia.org/wiki/Robot_d'indexation) 
ou un **robot d'indexation de texte** 
ou encore appelé un *moissonneur* en français
C'est un robot qui permet la constitution de gros corpus web textuels
issus de page web
autour d'une expression de recherche donnée 
de manière récurrente selon la fréquence souhaitée.

## A quoi ca sert?

Crawtext est un moissonneur d'informations issues des pages web. Il permet à un utilisateur de collecter les informations contenues dans les pages web autour d'un sujet et ce sur une fréquence régulière. Il permet ainsi de collecter ainsi des informations du web (acteurs, contenus des débats, liens entre acteur) de manière historicisée (dans son évolution) et centrée autour d'une question.

## Comment ca marche?
Crawtext est un moissonneur du web qui suit quelques principes simples. 

**[Ici](http://c24b.github.io/numi/cours1.html)** pour ceux qui le souhaite, un petit rappel utile pour comprendre le fonctionnement de ce robot sur ce qu'est le web, Internet et un site web. 

A partir d'une page web de départ appelée ```seed```, 
le robot crawler (qu'on compare à une araignée) visite la page et recupère dans la page html tous les liens disponibles qui prennent la forme de :
```<a href="lien>ancre</a>```

Il collecte et stocke les liens puis visite une à une les pages, récupère les liens, charge la page puis vérifie que l'expression de recherche est bien dans la page, si l'expression est trouvée il recommence le processus jusqu'à ce que plus une page ne soit  pertinente.
En pseudo code simplifié cela donnerait

```
queue = liste des urls de départ
tant que la queue de traitement n'est pas vide:
  pour chaque url:
    crawler le contenu de l'url
    si la requête est présente dans le contenu
      * on stocke l'information 
      * on ajoute les nouvelles urls citées dans la queue de traitement
      * on supprime l'url de la queue de traitement
    

```
## Stratégies de crawl
### Types de crawl
Crawtext est un crawler web qui possède plusieurs types de comportement. 
qui correspondent à plusieurs stratégies de crawl paramétrables par l'utilisateur:
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
    * une expression de recherche est alors indispensable au fonctionnement du crawl parce que les résultats de recherche constitue le point de départ du crawl
        
### Filtres
Plusieurs filtres additionnels sont proposés:

* un filtre de langue: le crawler selectionnera uniquement les textes qui correspondent à la langue selectionnée au format [ISO 639-1](https://fr.wikipedia.org/wiki/Liste_des_codes_ISO_639-1)

* un filtre de profondeur de crawl: le crawler arretera la recherche quand le nombre d'étape sera atteint.
      Ce filtre permet de réduire 
      les temps de traitement souvent très long
      et de controler les élargissements successifs 
      du périmêtre de recherche
* un filtre de recherche: 
le crawler selectionnera uniquement les textes qui correspondent à cette expression de recherche.
    
      Ce filtre est indispensable dans le cas d'un crawl autour 
      d'un sujet ou d'une thématique

Pour plus d'information sur les filtres: voir [Configuration](config.md)

### Fréquence
On peut programmer la **récurrence** du crawl en spécifiant une fréquence:
 * journalière
 * hebdomadaire 
 * ou mensuelle

Pour plus d'information sur les filtres: voir [Configuration](config.md)

## Limitations de Crawtext

### Interface web
Le crawler ne possède pas d'interface de configuration web pour le moment

### Type de données collectées
Le crawler Crawtext ne récupère pas tous les types d'information disponible sur le web. 

Sont exclus (pour le moment): 
* pdf
* fichiers
* videos
* sons 
* images
* flash 

En revanche, crawtext stocke à la fois:
* la **page html brute** 
* le **texte** de la page nettoyée
* des informations contextuelles supplémentaires

### Blockage des pubs et réseaux sociaux
Le crawler Crawtext bloque les pages commerciales (pubs, questionnaires, pop-ups) et les réseaux sociaux en utilisant un fichier AdBlocks qui n'est à ce stade pas configurable et n'est pas mis à jour automatiquement pour le moment.
Les sites webs dont les contenus sont chargés dynamiquement ne sont pas non plus supportés.

### Temps de traitement et capacité de stockage

En fonction du nombre d'url de départ, de la finesse de la requete, le crawler peut mettre de quleques heures à plusieurs jours à compléter ses tâches et les données collectées peuvent prendre énormément de place.
Il faut donc etre bien attentif à calibrer son crawl avant de le lancer et de tester pour le calibrer.

* Pour plus d'information sur l'état de l'art et les limitations: voir [Developper Guide](dev.md)

* Pour les améliorations voir [TODO](todo.md) et les modifications [CHANGELOG](changelog.md)
