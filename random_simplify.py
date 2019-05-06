# coding=utf-8
import os
import random
import syntaks
from estnltk import teicorpus


def simplifyRandom():
    counter = 0
    while True:
        path = 'korp/' + random.choice(os.listdir('korp'))
        fail = teicorpus.parse_tei_corpus(path, target=["artikkel", "alaosa", "tervikteos"])
        for _ in range(2):
            artikkel = random.choice(fail)
            laused = artikkel.sentence_texts
            for _ in range(25):
                lause = random.choice(laused)
                lihtsustatud, debug = syntaks.lihtsusta(lause)
                counter += 1
                if '__LIHTSUSTATUD__' in debug:
                    print("_________________________")
                    print("Esialgne lause\n", lause)
                    print("-------------------------")
                    print("Lihtsustatud lause\n", lihtsustatud)
                    print("_________________________")
                    print(str(counter) + ". lause, mida vaadati.")
                    return


simplifyRandom()
