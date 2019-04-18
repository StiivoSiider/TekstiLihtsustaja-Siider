#!/usr/local/bin/python
# coding: utf-8
import re
import sys
import html

import nltk

nltk.data.path.append("/home/veebid/ss_syntax/nltk_data")

from collections import defaultdict
from pprint import pprint
from estnltk import Text
from estnltk import synthesize
from estnltk.names import LAYER_CONLL
from estnltk.syntax.parsers import MaltParser
from custom_tokenizer import CustomWordTokenizer, CustomSentenceTokenizer

DEBUG = True
#DEBUG = False
LAUSE_PEASÕNAD = {"ROOT", "@FMV", "@IMV"}
ATRIBUUDID = {"@<AN", "@AN>", "@<NN", "@NN>",
              "@<DN", "@DN>", "@<INFN", "@INFN>",
              "@<KN", "@KN>", "@<P", "@P>", "@<Q", "@Q>"}

KWARGS = {
    "word_tokenizer": CustomWordTokenizer(),
    "sentence_tokenizer": CustomSentenceTokenizer()
}


def lihtsusta(esialgne_sisend):
    # Sisendi korrastamine
    sisend_sõne = eeltöötlus(esialgne_sisend)

    if DEBUG:
        print(sisend_sõne)

    sisendid = Text(sisend_sõne, **KWARGS)
    tulemus = ""
    onLihtsustatud = False
    for sisend in sisendid.sentence_texts:
        sisend = Text(sisend, **KWARGS)
        if DEBUG:
            print(sisend.word_texts)
            print(sisend.postags)
            parser = MaltParser()
            initial_output = parser.parse_text(sisend, return_type='conll')
            print('\n'.join(initial_output))

        for sõna in sisend.split_by("words"):
            otsing = None
            if re.match('.?"', sõna.text) and re.match('.*".?', sõna.text):
                otsing = re.search('^.?"(.*)".?$', sõna.text)
            elif re.match('.?\(', sõna.text) and re.match('.*\).?', sõna.text):
                otsing = re.search('^.?\((.*)\).?$', sõna.text)
            if otsing:
                sisu = otsing.group(1)
                sisend = sisend.replace(sisu, lihtsusta(sisu))

        verbi_loendur = 0
        for i in range(len(sisend.postags)):
            if sisend.postags[i] == "V":
                verbi_loendur += 1

        # Lõpetame lause vaatamise kui meil on ainult 1 verb, kuna sel juhul on ilmselt tegemist lihtlausega
        if verbi_loendur <= 1:
            print("__ÜKS TEGUSÕNA__")
            tulemus += sisend.text + " "
            continue

        sisend.tag_syntax()

        süntaksi_list = list(zip(sisend.word_texts, sisend[LAYER_CONLL]))
        if DEBUG: pprint(süntaksi_list)
        analüüsi_list = sisend.analysis

        siht_map = defaultdict(list)
        sõna_list = []
        mitte_juur_lausepeasõnad = []
        lause_peasõnad = []
        for i, element in enumerate(süntaksi_list):
            label, siht = element[1]['parser_out'][0]
            analüüs = analüüsi_list[i][0]
            pos = analüüs["partofspeech"]
            word = element[0]
            for char in {'"', '(', ')'}:
                if char in word:
                    word = re.sub('(^[.,!?]|[.,!?]$)', '', word)
                    break

            element_info = {"indeks": i, "word": word, "lemma": analüüs["lemma"], "form": analüüs["form"],
                            "pos": pos, "label": label, "target": siht}
            if label == "ROOT":
                lause_peasõnad.append(element_info)
            elif pos == "V" and label not in ATRIBUUDID or label in LAUSE_PEASÕNAD:
                mitte_juur_lausepeasõnad.append(element_info)
            if not analüüs["partofspeech"] == "Z":
                siht_map[siht].append(element_info)
            sõna_list.append(element_info)

        # Kui meil on mitu ROOT elementi, siis jätame selle vahele
        if len(lause_peasõnad) > 1:
            print("__MITU JUURSÕNA__")
            tulemus += sisend.text + " "
            continue

        lause_peasõnad.extend(mitte_juur_lausepeasõnad)
        lause_peasõnad_koopia = []
        lause_peasõnad_koopia.extend(lause_peasõnad)

        for verb in lause_peasõnad_koopia:
            for alluv in siht_map[verb["indeks"]]:
                if alluv in lause_peasõnad_koopia:
                    lause_peasõnad.remove(alluv)

        if len(lause_peasõnad) <= 1:
            print("__ÜKS PEASÕNA__")
            tulemus += sisend.text + " "
            continue

        # Muudame kõik asesõnad vastavateks nimisõnadeks. Kasutades nimisõna mitmesust ja asesõna käänet.
        # Kasutades nii asesõna mitmesust kui käänet on võimalik, et tulemus pole see, mida ootame. Näiteks võib ainsuse asemel olla mitmus.
        # Semantilise info puudumise tõttu, saame iga tegusõna kohta asendada vaid ühe asesõna.
        kasutatud_tegusõnad = set()
        kustutatavad = []
        for i, element in enumerate(sõna_list):
            if element["pos"] == "P":
                if not(i > 2 and sõna_list[i - 1]["pos"] == "Z" and sõna_list[i - 2]["pos"] in {"S", "H"}\
                        and element["lemma"] in {"kes", "mis"}):
                    siht = sõna_list[element["target"]]
                    if element["label"] == "@SUBJ":
                        subj_counter = 0
                        for alluv in siht_map[siht["indeks"]]:
                            if alluv["pos"] == "S" and alluv["label"] == "@SUBJ":
                                subj_counter += 1
                        if subj_counter > 0:
                            kustutatavad.append(element)
                            continue
                    if siht["pos"] != "V" or siht["target"] == -1:
                        continue
                    asendus = sõna_list[siht["target"]]
                    if asendus["pos"] not in {"S", "H"} or siht["indeks"] in kasutatud_tegusõnad:
                        continue
                else:
                    asendus = sõna_list[i - 2]
                    siht = sõna_list[element["target"]]
                    if siht["indeks"] in kasutatud_tegusõnad:
                        continue
                if siht["pos"] == "V":
                    kasutatud_tegusõnad.add(siht["indeks"])
                asendus_lemma = asendus["lemma"]
                asendus_pos = asendus["pos"]
                uus_sõnavorm = asendus["form"].split(" ")[0] + " "
                asesõna_sõnavorm = element["form"].split(" ")
                uus_sõnavorm += asesõna_sõnavorm[1 if len(asesõna_sõnavorm) > 1 else 0]
                süntees = synthesize(asendus_lemma, uus_sõnavorm, asendus_pos)
                asendus_lemma_asesõna_vormis = asendus_lemma
                if len(süntees) > 0:
                    asendus_lemma_asesõna_vormis = synthesize(asendus_lemma, uus_sõnavorm, asendus_pos)[0]
                element["word"] = asendus_lemma_asesõna_vormis
                element["lemma"] = asendus_lemma
                element["form"] = uus_sõnavorm
                element["pos"] = asendus["pos"]

        for kustutatav in kustutatavad:
            try:
                siht_map[sõna_list[kustutatav["target"]]["indeks"]].remove(kustutatav)
                sõna_list.remove(kustutatav)
            except:
                continue

        if DEBUG:
            pprint(dict(siht_map))
            pprint(lause_peasõnad)
            print("---------------------------------------------------")
            print(sisend_sõne)
            print("---------------------------------------------------")

        tulemus = ""
        for sõna in lause_peasõnad:
            lause = moodustaLause(sobitaMalli(sõna, siht_map))
            tulemus += lause.strip() + '. '
        onLihtsustatud = True

    if onLihtsustatud:
        print("__LIHTSUSTATUD__")
    return tulemus.strip()


def tagastaAlluvad(sõna, siht_map):
    sõna_list = []
    for alluv in siht_map[sõna["indeks"]]:
        if sõna["pos"] == "V" or alluv["pos"] != "V":
            sõna_list.append(alluv)
    return sõna_list


def sobitaMalli(sõna, siht_map):
    sõnade_list = []
    eel_list, järg_list = [], []
    # print(word, target_map[word["indeks"]])
    for alluv in siht_map[sõna["indeks"]]:
        if sõna["pos"] == "V" or sõna["label"] in LAUSE_PEASÕNAD or alluv["pos"] != "V" or alluv["pos"] == "V" and \
                        alluv["label"] in ATRIBUUDID:
            eelListi = ">" in alluv["label"] or alluv["label"] == "@J"
            eelListi = eelListi or alluv["label"] in {"@SUBJ", "@FCV", "@NEG", "@ADVL"}
            järgListi = "<" in alluv["label"] or sõna["pos"] == "V" and alluv["label"] in {"@PRD", "@ADVL", "@OBJ"}
            järgListi2 = sõna["label"] == alluv["label"] and alluv["label"] in {"@SUBJ", "@PRD", "@ADVL", "@OBJ"}
            järgListi3 = sõna["label"] == "ROOT" and sõna["pos"] == alluv["pos"] and alluv["label"] in {"@SUBJ", "@PRD", "@ADVL", "@OBJ"}
            järgListi = järgListi or järgListi2 or järgListi3
            if eelListi and not järgListi:
                eel_list.extend(sobitaMalli(alluv, siht_map))
            else:
                järg_list.extend(sobitaMalli(alluv, siht_map))
    sõnade_list.extend(eel_list)
    sõnade_list.append(sõna)
    sõnade_list.extend(järg_list)

    return sõnade_list


def moodustaLause(järjestus, lause=""):
    suur_algus = järjestus[0]["word"][0].capitalize()
    if len(järjestus[0]["word"]) > 1:
        suur_algus += järjestus[0]["word"][1:]
    järjestus[0]["word"] = suur_algus
    for sona in järjestus:
        lause += sona["word"] + " "
    return lause


def eeltöötlus(sisend):
    sisend = re.sub('\\\\', '', sisend) # Üleliigsete kaldkriipsude eemaldamine
    sisend = re.sub('\n', ' ', sisend)
    sisend = re.sub('[“”„«»]', '"', sisend)  # jutumärkide ühtlustamine
    #  sulgude ühtlustamine
    sisend = re.sub('[\[{]', '(', sisend)
    sisend = re.sub('[\]}]', ')', sisend)
    return sisend


if len(sys.argv) > 2 and sys.argv[2] == "arg":
    print('----',lihtsusta(sys.argv[1]))