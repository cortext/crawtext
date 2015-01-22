![http://www.cortext.net](http://www.cortext.net/IMG/siteon0.png)

CRAWTEXT
====

Crawtext est un module indépendant du Cortext manager qui permet la constitution de gros corpus web autour d'une thématique ou d'une expression de recherche donnée. La capitalisation de données web produites par Crawtext se fait sur une fréquence journalière, hebdomadaire ou mensuelle en fonction des besoins du projets et paramétrables par l'utilisateur. 
Crawtext est un crawler web par cible. Il stocke les pages web qui correspondent à l'expression de recherche demandée.


##Contexte

Les outils de constitution de corpus traditionnels sont nombreux (publications scientifiques, corpus de presse, rapports...), cependant il manquait aux chercheurs un moyen de collecter facilement des données du Web, de créer des archives issues d'Internet pour examiner la représentation d'un sujet ou d'une polémique en ligne.
Quelques crawlers ont déjà été développés mais aucun ne propose une approche par cible et par pertinence priviligiant la pag de départ.
Ils sont peu robustes ou difficile d'accès pour les non initiés ou parfois simplement limités dans leurs résultats et leur usage:
- 80legs version de (démo gratuite et limitée) [https://portal.80legs.com/users/sign_up?plan=basic] non ciblé
- Navicrawler (module Firefox d'archivage de sa navigation)
- TIRESIAS http://prosperologie.org (client lourd, non ciblé)
- Scrapy (installation et gestion complexe des règles, non ciblé, développement nécessaire)
- pyspider (développement nécessaire)


##Usage


Crawtext est un module d'extraction et d'archivage de pages Internet, il permet la constitution de corpus centrée autour d'un thème ou d'une expression.
Il permet donc la constitution d'une base de données constituées de pages internet et consolidées par un archivage régulier et son interrogation en l'important dans le Cortext Manager

##Fonctionnement

Crawtext est un crawler web ciblé: à partir d'une ou plusieurs urls, le crawler télécharge les pages examine le texte de la page et vérifie la correspondance avec le thème ou l'expression de recherche donnée. Si la page est pertinente, il ajoute les urls trouvées sur la page, télécharge les pages correspondants à ces urls et reproduit le traitement.

On obtient donc un ensemble de pages internet qui correspondent à une requete données et reliées entre elles par des urls communes.


##Architecture

Module indépendant du cortext manager, il est composé de plusieurs briques logicielles: 
* un systeme de gestion de tâches (parametrages, crawl, export, reporting) extensible selon les besoins
* une API de crawl (interrogeable en ligne de commande ou intégrable dans des scripts externes) 
* une interface web de paramêtrage en accès restreint. 

##Politique d'accès et limitations

Le développement de ce module a été fait de manière indépendante du cortext manager et son utilisation controlée pour plusieurs raisons: le volume de données, l'utilisation de la bande passante et les éventuelles questions juridiques de stockage de données et de téléchargement de pages web. 

L'interface web n'est disponible qu'aux utilisateur muni d'un compte et d'un mot de passe

Crawtext limite le nombre de résultats à 200.000, une fois ce résultat atteint il supprime les pages de la profondeur maximum atteinte.

Le nombre de résultats donnés par BING est limité à 1000 résultats, par défaut l'application en récupère 500 mais cette limitation est paramêtrable.

Le crawler n'accepte que les contenus html et filtre en amont les pages commerciales référencées par le module AdBlockPlus

Pour optimiser le temps de traitement des crawls lancés à date fixe, les urls déjà traitées et de nouveau identifiées
ne sont pas retraitées dans leur intégralité mais mis à jour avec la date du crawl.


Aperçu des fonctionnalités
=

Crawtext est un script développé en Python 2.7 avec une base de données Mongo.

Le gestionnaire de tâches consiste en l'interrogation d'une base de données mongo 
qui contient la liste de tâches affecté à chaque projet (crawl/report/export).
A chaque projet est affecté une liste de paramêtres, un historique des modifications dans cette base 
Chaque projet dispose :
- d'un dossier spécifique qui contient:
    - rapports d'avancement et statistiques(.txt) 
    - exports des données (csv/json ET zip) contenu dans une BDD spécifique
        - resultats
        - sources
        - logs d'erreur

L'API permet:
- la consultation des tâches 
- la consulation et modification des paramêtres de chaque projet
- la gestion d'un crawl:
    - configuration (ajout/modification/suppression de paramêtres)
    - start
    - stop
    - delete
- la création et l'envoi de rapport sur un projet
- la création d'export

L'appel à l'API peut se faire en ligne de commande ou utilisée comme script ad hoc.
Le paramétrage et la création d'un crawl peuvent se faire via l'interface web.


##Utilisation
=

Pour lancer un crawl seules 3 paramêtres sont obligatoires:
- un nom de projet
- une requete (Cf Syntaxe de requete)
- une ou plusieurs urls de départs: les sources du crawl


###Interface web 

La création et le paramêtrage d'un crawl peut se faire via un simple formulaire en ligne 
pour les utilisateurs muni d'un compte et d'un mot de passe.


- Nom du projet
- Requete:
    La syntaxe de recherche accepte plusieurs opérateurs:
    - AND OR NOT 
    - recherche exacte: "" 
- Sources de départ:
Il existe plusieurs manières d'ajouter les sources de départ:
    - ajouter une url
    - ajouter plusieurs urls via un fichier .txt 
    - ajouter les x urls issus d'une recherche BING en donnant la clé API (nombre de résultats modifiable <=1000) 
        defaut: 500

Plusieurs options peuvent être ajoutées:
- un mail pour l'envoi par mail des rapports (disponible aussi dans le dossier du projet)
- la profondeur de crawl 
    defaut: 100
- le format de l'export (csv/json) 
    defaut: json
- la récurrence du crawl 
    defaut: tous les mois

###Ligne de commande


L'intégralité du projet crawtext peut être téléchargé et installé sur son propre serveur.
Le seul prérequis est d'avoir préalablement installé MongoDB sur sa machine
Les sources de l'application sont disponibles sur Github à cette adresse:
[https://github.com/cortext/crawtext]
Pour les détails d'installation et d'utilisation voir la documentation technique 
[https://github.com/cortext/crawtext/blob/master/README.md]



##Implémentation technique

Crawtext est développé en Python 2.7, les bases de données de gestion des tâches et de stocakges des résultats est MOngoDB
Hormis l'installation de mongo, l'ajout du scheduler en crontab et l'éventuelle modification de l'adresse du serveur de mail
Tous les modules externes utilisés sont des modules python disponible via pip

###Paramêtrage

####Interface web

L'interface web est développée avec un mini serveur HTTP en python bottle.py un template bootstrap et des scripts en javascript développé en interne. 
####Ligne de commande
La gestion en ligne de commande utilise le module python docopt
Toutes les valeurs acceptées par la ligne de commande sont listées dans la documenation technique

####API 
L'appel direct à l'API via un autre script utilise l'objet Worker() présent dans le fichier wk.py

####Ajout des sources
- Ajout de sources de départ via Bing:
    Requete GET sur l' API Search V2 de BING: pour obtenir sa clé API:
     [https://github.com/cortext/crawtext/blob/master/README.md]
     Suite aux limitations de l'api de BING et la découverte de l'aspect aléatoires du nmbre de rsultats maximum: la limitation par défaut du nombre de résultats retourné est de 500 (en théorie <=1000)

###Téléchargement et extraction
- Téléchargement et extraction de pages web: requests (pas d'utilisation de proxies ni de multithreading des urls, timeout de 5sec, nombre d'essai 2)

- Extraction et enrichissement des résultats de la page: BeautifulSoup

    Après les tests de plusieurs solutions d'extraction d'article:
        - newspaper
        - python-goose
        - boilerpipe
    aucune ne s'est avérée capable d'extraire proprement les articles issu des blogs. Le calcul de pertinence de l'article étant faussé nous avons finalement opté pour un extract brute de texte entier de la page html. 
- Enrichissement des résultats de l'url: tldextract + module spécifique inspiré de Newspapers + Scrapy

###Filtrage et calcul de pertinence
- Filtrage des urls non pertinentes: 
    - format html uniquement
    - protocol http/https uniquement
    - url non présentes dans le fichier AdBlockPlus (non mis à jour automatiquement)
- Calcul de pertinence des pages:
    - recherche exacte: ("") utilisation du module de regex
    - recherche combinée: moteur d'indexation Whoosh et de son parser de requete par défaut

###Stockage et export

- La manipulation et l'accès au base de données MongoDB utilise le module pymongo 
encapsulé dans un module de gestion interne database/database.py

L'export est disponible via la fonction export et possède plusieurs paramêtres facultatifs:
- le format d'export: (csv, json) par defaut: json
- le type de données à exporter: results sources logs par défaut: les trois

A note que l'export csv pour respecter l'aspect tabulaires des données est incomplet.

* Gestionnaire de tache:
Chaque tache est présente dans une base de données appelée crawtext_jobs et stockés dans la même "table" 
ou collection appelée "job". 
Elle sont stockées par tache comme suit:
```
{
    "_id" : ObjectId("54bf8e4cdabe6e1383ae172f"),
    "status" : [
        "True",
        "True",
    ],
    "project_name" : "pesticides3",
    "date" : [
        ISODate("2015-01-21T12:32:28.322Z"),
        ISODate("2015-01-28T01:00:00.0000")
    ],
    "name" : "pesticides3",
    "creation_date" : ISODate("2015-01-21T12:32:28.322Z"),
    "directory" : "./crawtext/crawtext/projects/pesticides",
    "key" : "J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o",
    "action" : [
        "create",
        "crawl"
    ],
    "query" : "pesticides AND DDT",
    "type" : "crawl",
    "msg" : [
        "Ok",
        "Ok",
    ]
}
```
* Base de données projet:
Chaque projet dispose de sa propre base de données avec 3 "tables" ou "collections":
- sources : voir [https://github.com/cortext/crawtext/blob/master/examples/sources_example.json]
- results: [https://github.com/cortext/crawtext/blob/master/examples/results_example.json]
- logs [https://github.com/cortext/crawtext/blob/master/examples/logs_example.json]


###Reporting


- Serveur de mail: gmail par défaut (ajout d'un user and passw) 
    L'appel à un autre serveur SMTP est modifiable dans le code utils/mail.py
- Le moteur de templating est Jinja
- Les statistiques de traitement sont exposés dans le module de gestion des bases de données développé en interne
    (database/database.py)

###Scheduler

Le module de gestion de la des projest par jour/semaine/mois s'effectue à partir de la date de crawl
Il nécessite la programmation du script scheduler.py en crontab qui sera lancé tous les jours, ce script appelle la base de données de tache et vérifie les dates de crawl. 
Exemple de configuration de crontab pour un projet pesticides où le dossier github de crawtext serait stocké dans /srv/scripts
```
    # m h  dom mon dow   command
    0 1 * * * python /srv/scripts/crawtext/crawtext/crawtext.py RRI_0 start
    0 * * * 1 python /srv/scripts/crawtext/crawtext/crawtext.py RRI_0 report
```

Pour optimiser les crawls lancé à date fixe, les urls déjà traitées et de nouveau identifiées
ne sont pas retraitées dans leur intégralité mais la date de crawl est ajoutée.


##Evolutions et Features


*Interface web:
    * Authentification pour l'accès à l'interface web
    * Ajout d'une url pour le téléchargement des résultats
    * Ajout d'une alerte avant suppression du projet
*API:
    * Extension des formats acceptés: téléchargement de pdf (images, videos?)
    * Prise en compte de la langue de la page
    * Ajout d'une option de crawl centré sur un seul site
    * Détection et extraction des articles
    * Parallélisation des requetes HTTP
    * Proxys tournants et anonymisation des requetes

