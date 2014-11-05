# -*- coding: utf-8 -*-
 
import time
from time import mktime
from datetime import datetime
from multiprocessing import Process, Queue, TimeoutError 
import feedparser
 
# cette fonction va être utilisée comme worker
# elle va lancer un process qui tourne en boucle et vérifie de manière
# régulière si il y a des flux à mettre à jour
def mettre_a_jour_les_flux(request_queue, extract_queue):
 
    last_update = {}
 
    while True: # une bonne boucle infinie pour la main loop
        try:
            # on vérifie si il y a un message dans la queue pendant 0.1 secondes
            # si oui, on parse le flux (sinon, ça raise une TimeoutError)
            url = request_queue.get(0.1)
            
            
            articles = []
            
            
            # pour chaque article, on vérifie si la date de parution est
            # antérieur au dernier check, et si oui, on le déclare
            # "nouvel article"
            for doc in request(item):
                if doc is not False:
                    articles.append(url, doc.txt)
                
 
            # on balance tous les nouveaux articles dans la queue
            if nouveaux_articles:
                queue_de_mises_a_jour_des_flux.put((url, nouveaux_articles))
 
            last_update[flux] = datetime.now()
 
        # en cas de time out on repart sur un tour de boucle
        # si l'utilisateur fait CTRL+C sur le worker principal, il sera
        # broadcasté ici, donc on le catch et on exit proprement
        except TimeoutError:
            pass
        except KeyboardInterrupt:
            sys.exit(0)
 
 
# worker très basique qui demande la mise à jour de tous les flux
# c'est bourrin, mais c'est pour l'exemple on vous dit !
def demander_la_mise_a_jour_des_flux(queue_de_flux_a_mettre_a_jour, flux_rss):
    """
        Demande la mise à jour des flux toutes les 5 minutes
    """
 
    # pareil, petite boucle infinie, temporisation et gestion du CTRL + C
    # en gros on ne fait que remplir la queue toutes les 5 minutes
    # avec des urls
    while True:
 
        try:
            for flux in flux_rss:
                queue_de_flux_a_mettre_a_jour.put(flux)
 
            time.sleep(300)
 
        except KeyboardInterrupt:
            sys.exit(0)
 
 
# très important ce if, sinon sous windows le module sera importé plusieurs
# fois et lancera ce bloc plusieurs fois
if __name__ == '__main__':
 
    # les flux à mettre à jour, RAS
    flux_rss = (
        'http://sametmax.com/feed/',
        "http://sebsauvage.net/links/index.php?do=rss",
        "http://charlesleifer.com/blog/rss/",
        "http://xkcd.com/rss.xml"
    )
 
    # les queues. Ces objets sont comme des listes partageables entre
    # les workers, sur lesquelles on pourrait faire uniquement insert(0, elem)
    # (ici put(elem)) et pop() (ici get()). Des FIFO thread safe quoi.
    queue_de_flux_a_mettre_a_jour = Queue()
    queue_de_mises_a_jour_des_flux = Queue()
 
    # ici on créé nos workers: on dit quelle fonction lancer avec quels
    # arguments. Nos arguments ici sont essentiellement les queues,
    # puisque c'est ce qui va nous permettre de partager les infos
    # entre les process (qui sont sinon isolés les uns des autres)
    worker_qui_met_a_jour_les_flux = Process(target=mettre_a_jour_les_flux,
                                             args=(queue_de_flux_a_mettre_a_jour,
                                                   queue_de_mises_a_jour_des_flux))
 
    worker_qui_demande_la_mise_a_jour = Process(target=demander_la_mise_a_jour_des_flux,
                                                args=(queue_de_flux_a_mettre_a_jour,
                                                      flux_rss))
 
    # On démarre les workers, et à partir de là, 2 processus sont créés
    # et lançant chacun une fonction, les boucles infinies tournent joyeusement
    # et une personne est agressée toutes les 7 secondes à New York aussi,
    # mais on s'en fout dans notre cas présent.
    # Bien faire gaffe que les fonctions soient capables de tourner à vide :-)
    worker_qui_met_a_jour_les_flux.start()
    worker_qui_demande_la_mise_a_jour.start()
 
    # et voici notre worker principal, qui pop les nouveaux flux tout
    # frais, et les affiche à l'écran
    try:
        while True:
            try:
                feed, articles = queue_de_mises_a_jour_des_flux.get(0.2)
                print "Voici les derniers articles de %s :" % feed
                for article in articles:
                    print "- %s" % article
            except TimeoutError:
                pass
 
    except KeyboardInterrupt:
        pass
    finally:
        # si la boucle while s'arrête d'une manière ou d'une autre
        # on attend que les autres processus s'arrêtent avant de quitter
        # En vrai on mettrait beaucoup plus de code que ça, une file
        # de controle, peut être un handler de SIGTERM, etc
        # là on va à l'essentiel
        worker_qui_met_a_jour_les_flux.join()
        worker_qui_demande_la_mise_a_jour.join()
 
    print "Fin des haricots"