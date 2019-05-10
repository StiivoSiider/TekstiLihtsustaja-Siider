#!/usr/local/bin/python
# coding: utf-8
"""
Korpuse automaattestija, mis käib läbi kogu etteantud korpuse ning kogub lihtsustamistulemuste kohta statistikat
Autor: Stiivo Siider
"""
import estnltk
import re
import requests
from estnltk import Text
from estnltk import teicorpus


def testCorp():
    korpus = teicorpus.parse_tei_corpora("./tei_test", suffix=".tei", target=["artikkel", "alaosa", "tervikteos"])
    errorCounter = 0
    errorSents = []
    errors = []
    totalCounter = 0
    simplifiedCounter = 0
    verb1Counter = 0
    main1Counter = 0
    rootCounter = 0
    for artikkel in korpus:
        for sentence in artikkel.sentence_texts:
            try:
                r = requests.get('http://prog.keeleressursid.ee/ss_syntax/?l=' + sentence)
                tulemus = re.sub('.*?<pre>(.*?)</pre>.*?', r'\1', r.text, flags=re.DOTALL)
                info, lause = tulemus.strip().split("---- ")
                totalCounter += 1
                if "__ÜKS TEGUSÕNA__" in info:
                    verb1Counter += 1
                elif "__MITU JUURSÕNA__" in info:
                    rootCounter += 1
                elif "__ÜKS PEASÕNA__" in info:
                    main1Counter += 1
                if "__LIHTSUSTATUD__" in info:
                    simplifiedCounter += 1
                    print(sentence)
                    print(lause)
                    print("-----------------------------")

            except Exception as e:
                errorCounter += 1
                errorSents.append(sentence)
                errors.append(str(e))

    print("Total", totalCounter)
    print("Simplified", simplifiedCounter)
    print("Stopped 1 verb", verb1Counter)
    print("Stopped 1 main", main1Counter)
    print("Stopped 2+ root", rootCounter)

    print("Errors", errorCounter)
    for i, sent in enumerate(errorSents):
        print("Error sentence", sent)
        print("Error message", errors[i])
        print()


testCorp()
