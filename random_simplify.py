# coding=utf-8
"""
Juhusliku lause lihtsustaja
Autor: Stiivo Siider

Skript, mis käsurealt käivitades võtab endaga samas kaustas olevast kaustast "korp" suvalise korpusefaili
ning võttes juhuslikult lauseid annab neid lihtsustajale ette.

Igast korpusefailist vaadeldakse kuni 50 lauset, mille järel loetakse sisse uus korpus.
"""
import os
import random
import syntaks
from estnltk import teicorpus


def simplifyRandom():
    counter = 0
    while True:
        path = 'korp/' + random.choice(os.listdir('korp'))
        fail = teicorpus.parse_tei_corpus(path, target=["artikkel", "alaosa", "tervikteos"])
        for _ in range(5):
            artikkel = random.choice(fail)
            laused = artikkel.sentence_texts
            for _ in range(10):
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
