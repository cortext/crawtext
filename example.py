from crawtext import Crawtext
dict_params = {"url":"http://www.hoaxbuster.com/", "max_depth":"5"}
c = Crawtext("hoax")
c.start(dict_params)
