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
- Discovery: Simple requête web qui ajoute les nouvelles url à la source avec date d'ajout / suppression
- Périmêtre défini à une liste de sources fixes qui ne bouge pas

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
> Problème de Httplib terminé (Problème dans l'envoi des headers)
Etat: Terminé

###Nettoyage des textes:
- Boilerpipe (Problème de portage des lib)
- Test de Goose: intégration de la logique de Goose (==> Goose)
- Extract du flux RSS (NIY)
- Nettoyage final en regex (NIY)
Etat: 99%
###Nettoyage des urls
Url relative vs url absolue
Etat: Terminé

###Base de données:
- Ecriture des résultats au fur et à mesure.
- Ajout d'un champ nom du projet pour création d'une BDD correspondante structurée comme suit:
	
	* Collection: **"sources"**
		    
		    {
		    
		    "url": "www.example.com", 
		    
		    "date": timestamp(2005-10-30 T 23:00), 
		    
		    "method":"sourcing",
		    
		    } 
	
	* Collection: **"results"** 
		
		      {
		 
		    "url": "www.example.com",
		 
		    "pointers":["www.example4.com", "www.example5.com","www.example6.com"],
		 
		    "outlinks":["www.example4.com", "www.example5.com","www.example6.com"],

		    "backlinks":["www.example4.com", "www.example5.com","www.example6.com"],
		 
		    "title": "titre de la page",
		 
		    "source":"Le texte nettoyé de la page", 
		 
		    "pubdate":timestamp(2005-10-30),
		 
		    "crawldate": timestamp(2005-10-30 T 23:00),
		
		      }
	
	* Collection: **"report"**
		
		      {
		 
		    "url": "www.example.com",
		 
		    "error_code":404,
		 
		    "error_description": "Page not found",
		
		      }

>Remarque: ajout des dates au moment de l'implémentation de la récurrence (à vérifier)


Etat d'avancement : 100%

###Multiprocessing:
Passage d'un traitement par thread à un tratement plus léger par multiprocessing. 
>Refactorisation du code

###Ajout de fréquence et périmêtre pour le crawl
####Fréquence d'execution du crawl défini par l'utilisateur:
Permettre l'exploration à intervalle
* 3 options :	
	** à definir  

> See python-cron
Etat: 0%

####Périmêtre d'execution du crawler défini par l'utilisateur:

* Mode découverte: à chaque execution du crawler nouvelle recherche par mot clé, insertion cumulative dans la table source de la nouvelle url avec sa date d'ajout et la méthode d'ajout (sourcing/ discovery)

* Mode sourcing: à la première execution du crawler, création d'une bddd source puis simple execution du crawler sur ces données sources la méthode d'ajout par dafut est sourcing


==> A valider
Etat: 0%

####Autres questions

- Intégration et stockage des PDF?
- Gestion des liens réciproques? (Base intégrée mais nécessite ensuite une réinterprétation de la BDDB => Script à part pour remonter le chemin inverse))





 






 
