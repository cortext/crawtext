#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
import os
#from utils import encodeValue

class Query(object):
    def __init__(self, query, directory="", debug=True):
        self.debug = debug

        if directory != "":
            #if self.debug: print "no directory"
            dir_index = os.path.join(directory, "index")

            if not os.path.exists(dir_index):
                os.makedirs(dir_index)

        else:
            if not os.path.exists("index"):
                os.makedirs("index")

        schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
        self.ix = create_in(dir_index, schema)
        self.q = unicode(query)
        self.query= MultifieldParser(["title", "content"], schema=schema).parse(self.q)

        #self.query = QueryParser("content", self.ix.schema).parse(query)


    def index_doc(self, doc):
        with self.ix.writer() as writer:
            writer.add_document(title=doc['title'], content=doc['content'])
        return writer

    def rematch(self,xpr, doc):
        # if self.debug: print re.findall(xpr, (unicode(doc['content'])).lower())
        if len(re.findall(xpr, doc['content'].lower())) == 0:
            return False
        return True

    def match(self,doc):
        if '"' in self.q:
            self.query = re.sub('"', '', (self.q).lower())
            xpr = re.compile(self.query)
            return self.rematch(xpr, doc)
        else:
            self.index_doc(doc)
            with self.ix.searcher() as searcher:
                results = searcher.search(self.query)
                w = self.ix.writer()
                w.delete_document(0)
                try:
                    self.hit = results[0]
                    return True
                except IndexError:
                    self.hit = None
                    return False
if __name__=="__main__":
    #test
    #~ q = Query("(COP21) OR (COP 21)", directory="index")
    #~ doc = {'content': u'  CUBE 2020 labellis\xe9 COP21 Le concours CUBE 2020 organis\xe9 par l\'IFPEB vient d\'\xeatre labellis\xe9 COP21 par le comit\xe9 de labellisation pr\xe9sid\xe9 par madame S\xe9gol\xe8ne Royal, Ministre de l\u2019\xc9cologie, du D\xe9veloppement durable et de l\u2019\xc9nergie !  CUBE 2020 permet \xe0 ses participants d\u2019enclencher, poursuivre ou approfondir ses \xe9conomies d\u2019\xe9nergies en mobilisant la bonne exploitation et les bons usages des b\xe2timents. Le concours a \xe9t\xe9 jug\xe9 comme une solution exemplaire pour rentrer dans le vif du sujet des \xe9conomies d\u2019\xe9nergie gr\xe2ce aux actions de terrain. COP21, c\'est la Conf\xe9rence des Parties - Convention Cadre des Nations Unis sur le Changement Climatique - qui se tiendra pour sa 21\xe8me \xe9dition \xe0 Paris d\xe9but septembre. Au-del\xe0 des accords internationaux, essentiels au niveau mondial pour maintenir le cap au niveau politique, il y a les programmes d\u2019action de terrain qui rendent concrets et r\xe9els la transition \xe9nerg\xe9tique: CUBE 2020 est l\u2019un d\u2019entre eux. Merci \xe0 tous ceux qui participent \xe0 ce beau projet ! Les organisateurs \xa0 Tout sur la COP21 : www.cop21.gouv.fr Tous les projets labellis\xe9s sur ce lien. Une excellente infographie pour tout comprendre de la COP21 sur ce lien.    CUBE 2020 SAISON 2 lanc\xe9 au Sommet Mondial "Climat et Territoires" de Lyon Le \xab\xa0top d\xe9part\xa0\xbb de la deuxi\xe8me \xe9dition de CUBE2020 a \xe9t\xe9 donn\xe9 officiellement ce jour depuis le \xa0Sommet Mondial \xab Climat et Territoires\xbb de Lyon, pr\xe9paratoire \xe0 la COP21, par le Plan B\xe2timent Durable, les parrains et les du programme et les organisateurs. Le laur\xe9at de la pr\xe9c\xe9dente \xe9dition a r\xe9alis\xe9 plus de 20% d\u2019\xe9conomies en un an et les inscriptions sont encore ouvertes.  De m\xeame qu\u2019\xab\xa0un chemin de mille lieues commence toujours par un premier pas\xa0\xbb, l\u2019atteinte de nos objectifs climatiques aux horizons 2020 et 2030 passe par la mobilisation concr\xe8te des personnes sur le terrain et la mise en place de premi\xe8res actions r\xe9elles. \xa0  Lire la suite : CUBE 2020 SAISON 2 lanc\xe9 au Sommet Mondial "Climat et Territoires" de Lyon  ', 'title': u''}
    #~ print q.match(doc)
    pass
