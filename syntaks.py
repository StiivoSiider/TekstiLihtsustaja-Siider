#!/usr/bin/env python

# Impordime NLTK paketi, kuna tahame muuta nltk_data kausta asukohta (vajalik EstNLTK töötamiseks)
import nltk
nltk.data.path.append("/home/veebid/ss_syntax/nltk_data")


import sys
from estnltk import Text
from estnltk.names import LAYER_CONLL
from pprint import pprint

# Muudame lause EstNLTK lauseks
sisend = Text(sys.argv[1])

# Süntaksianalüüs
sisend.tag_syntax()
pprint(sisend[LAYER_CONLL])
