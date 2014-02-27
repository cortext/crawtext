#CRAWTEXT

##SPECIFICATIONS
Crawler pour l'analyse de corpus web.

=>Définition du corpus d'études
- un fichier texte (une url par ligne)
- une requête web (résultats de recherche BING)
- approche combinée ( fichier source + recherche)

=> Définition de la fréquence des crawls
*Définir la fréquence
*Définir le périmêtre
- Discovery: Simple requête web
- Périmêtre défini à une liste de sources fixes

=> Résultats
Une base de donnée (exportable en JSON) avec trois tables:

- Résultats: 
	Url de départ, titre, article en texte, urls sortantes
- Erreurs de traitement: 
	Url, code erreur, description
- Sources:
	Url, date d'ajout, méthode d'ajout
 
##ROADMAP
###Gestion des erreurs:
- Traiter l'intégralité des erreurs de téléchargement de pages
- Intégrer un rapport sur les urls erronées dans la base de données (table distincte des résultats)

>Reste une erreur sur le chargement de certaines pages à voir avec HttpLib et le formattage de la requete à analysser dans les rapports d'erreurs

Etat: Terminé

###Base de données:
- Ecriture des résultats au fur et à mesure.
- Ajout d'un champ nom du porjet pour création d'une BDD correspondante structurée comme suit:
	
	* Collection: **"sources"**
		    
		    '{
		    
		    "url": "www.example.com", 
		    
		    "date": timestamp(2005-10-30 T 23:00), 
		    
		    "method":(sourcing OR discovery)
		    
		    }' 
	
	* Collection: **"results"** 
		
		'{
		 
		 "url": "www.example.com",
		 
		 "pointers":["www.example4.com", "www.example5.com","www.example6.com"],
		 
		 "outlinks":["www.example4.com", "www.example5.com","www.example6.com"],
		 
		 "title": "titre de la page",
		 
		 "source":"Le texte nettoyé de la page", 
		 
		 "pubdate":timestamp(2005-10-30),
		 
		 "crawldate": timestamp(2005-10-30 T 23:00),
		
		}'
	
	* Collection: **"report"**
		
		'{
		 
		 "url": "www.example.com",
		 
		 "error_code":404,
		 
		 "error_description": "Page not found",
		
		}'

>Remarque: ajout des dates au moment de l'implémentation de la récurrence


Etat d'avancement : 70%

###Multiprocessing:
Passage d'un traitement par thread à un tratement plus léger par multiprocessing. 
>Refactorisation du code

###Ajout de fréquence et périmêtre pour le crawl
####Fréquence d'execution du crawl défini par l'utilisateur:
Permettre l'exploration à intervalle
* 3 options :	
	* tous les jours pendant 1 mois 
	* toutes les semaines pendant 1 mois
	* une fois par mois pendant 6 mois

>là on peut aussi ajouter par heure, par minutes, le lundi mardi jeudi par exemple  qu'on veut 
>mais je suis pas sure que ce soit vraiment nécessaire et autant ne pas embrouiller l'utilisateur

Etat: 0%

####Périmêtre d'execution du crawler défini par l'utilisateur:

* Mode découverte: à chaque execution du crawler nouvelle recherche par mot clé, insertion cumulative dans la table source de la nouvelle url avec sa date d'ajout et la méthode d'ajout (sourcing/ discovery)

* Mode sourcing: à la première execution du crawler, création d'une bddd source puis simple execution du crawler sur ces données sources la méthode d'ajout par dafut est sourcing


Etat: 0%




 






 
