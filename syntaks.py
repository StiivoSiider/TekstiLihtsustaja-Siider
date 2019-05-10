#!/usr/local/bin/python
# coding: utf-8
"""
Teksti lihtsustaja, mis rakendab süntaktilist lihtsustamist
Autor: Stiivo Siider

Lihtsustaja peamiseks kasutusviisiks on käsurealt käsklusega:

> python3 syntaks.py '<Lihtsustatav lause>' arg
"""
import html
import nltk
import re
import sys
from copy import deepcopy

nltk.data.path.append("/home/veebid/ss_syntax/nltk_data")

from collections import defaultdict
from pprint import pformat
from estnltk import Text, synthesize
from estnltk.names import LAYER_CONLL
from estnltk.syntax.parsers import MaltParser
from custom_tokenizer import CustomWordTokenizer, CustomSentenceTokenizer



DEBUG = True
# DEBUG = False
LAUSE_PEASÕNAD = {"ROOT", "@FMV"}
TEGUSÕNAD = {"@FMV", "@FCV", "@IMV", "@ICV", "@Vpart", "@VpartN", "@X", "@NEG"}
ATRIBUUDID = {"@<AN", "@AN>", "@<NN", "@NN>",
              "@<DN", "@DN>", "@<INFN", "@INFN>",
              "@<KN", "@KN>", "@<P", "@P>", "@<Q", "@Q>"}

KWARGS = {
    "word_tokenizer": CustomWordTokenizer(),
    "sentence_tokenizer": CustomSentenceTokenizer()
}


def lihtsusta(esialgne_sisend):
    """
    Peameetod sisendi lihtsustamiseks

    :param str esialgne_sisend: lihtsustatav sisend
    :return: paar lihtsustatud sisendist ning lisainformatsioonist
    """
    debug_info = ""
    # Sisendi korrastamine
    sisend_sõne = eeltöötlus(esialgne_sisend)

    if DEBUG:
        debug_info += str(sisend_sõne) + '\n'

    sisendid = Text(sisend_sõne, **KWARGS)
    tulemus = ""
    onLihtsustatud = False
    for sisend in sisendid.sentence_texts:
        # ANALÜÜS
        sisend = Text(sisend, **KWARGS)
        if DEBUG:
            debug_info += str(sisend.word_texts) + '\n'
            debug_info += str(sisend.postags) + '\n'
            parser = MaltParser()
            initial_output = parser.parse_text(sisend, return_type='conll')
            debug_info += '\n'.join(initial_output) + '\n'

        for sõna in sisend.split_by("words"):
            otsing = None
            if re.match('.?".*".?', sõna.text):
                otsing = re.search('^.?"(.*)".?$', sõna.text)
            elif re.match('.?\(.*\).?', sõna.text):
                otsing = re.search('^.?\((.*)\).?$', sõna.text)
            if otsing:
                sisu = otsing.group(1)
                rekursioon = lihtsusta(sisu)
                debug_info += rekursioon[1] + '\n'
                sisend = sisend.replace(sisu, rekursioon[0])

        verbi_loendur = 0
        for i in range(len(sisend.postags)):
            if sisend.postags[i] == "V":
                verbi_loendur += 1

        # Lõpetame lause vaatamise kui meil on ainult 1 verb, kuna sel juhul on ilmselt tegemist lihtlausega
        if verbi_loendur <= 1:
            debug_info += "__ÜKS TEGUSÕNA__\n"
            tulemus += sisend.text + " "
            continue

        # Suur lausealgustäht jäetakse alles vaid lühendite ning pärisnimede puhul.
        if sisend.postags[0] not in {"H", "Y"}:
            sisend.word_texts[0] = sisend.word_texts[0].lower()

        sisend.tag_syntax()

        süntaksi_list = list(zip(sisend.word_texts, sisend[LAYER_CONLL]))
        if DEBUG:
            debug_info += pformat(süntaksi_list)
        analüüsi_list = sisend.analysis

        siht_map = defaultdict(list)
        sõna_list = []
        mitte_juur_lausepeasõnad = []
        lause_peasõnad = []
        tegusõnad = []
        for i, element in enumerate(süntaksi_list):
            label, siht = element[1]['parser_out'][0]
            analüüs = analüüsi_list[i][0]
            pos = analüüs["partofspeech"]
            word = element[0]
            for char in {'"', '(', ')'}:
                if char in word:
                    word = re.sub('(^[.,!?]|[.,!?]$)', '', word)
                    break

            if re.match('.?\(.*\).?', word):
                label = "@<"
                pos = "SLG"
                if analüüsi_list[siht][0]["partofspeech"] == "Z":
                    siht -= 1 if siht > 0 else 0

            element_info = {"indeks": i, "word": word, "lemma": analüüs["lemma"], "form": analüüs["form"],
                            "pos": pos, "label": label, "target": siht}
            if DEBUG:
                debug_info += str(element_info) + '\n'
            if label == "ROOT":
                lause_peasõnad.append(element_info)
            elif label == "@FMV":
                mitte_juur_lausepeasõnad.append(element_info)
            if label in TEGUSÕNAD:
                tegusõnad.append(element_info)
            if not pos == "Z":
                siht_map[siht].append(element_info)
            sõna_list.append(element_info)

        # Kui meil on mitu ROOT elementi, siis jätame lause vahele
        if len(lause_peasõnad) > 1:
            debug_info += "__MITU JUURSÕNA__\n"
            tulemus += sisend.text + " "
            continue

        tegusõnad = lause_peasõnad + tegusõnad
        lause_peasõnad.extend(mitte_juur_lausepeasõnad)

        if DEBUG:
            debug_info += pformat(tegusõnad)
            debug_info += pformat(lause_peasõnad)

        # TRANSFORMATSIOON
        for verb in tegusõnad:
            for alluv in siht_map[verb["indeks"]][:]:
                if alluv in lause_peasõnad:
                    peasõnadEraldatud = False
                    if not (verb["label"] == "ROOT" and verb["pos"] != "V"):
                        for alluva_alluv in siht_map[alluv["indeks"]]:
                            if alluva_alluv["indeks"] > verb["indeks"] and (
                                                alluva_alluv["label"] == "@J" and alluva_alluv["lemma"] in {"ja", "ning"} or
                                                alluva_alluv["pos"] == "P" and alluva_alluv["lemma"] in {"kes", "mis"}):
                                subjekt = leiaOtseneSubjekt(alluv, siht_map)
                                if subjekt is None:
                                    uus_subjekt = leiaTegusõnaSubjekt(verb, siht_map, sõna_list)
                                    if uus_subjekt != None:
                                        peasõnadEraldatud = True
                                        alluva_alluv.update(uus_subjekt)
                                else:
                                    peasõnadEraldatud = True
                                    if alluva_alluv != subjekt:
                                        siht_map[alluv["indeks"]].remove(alluva_alluv)
                                if peasõnadEraldatud:
                                    siht_map[verb["indeks"]].remove(alluv)
                                break
                    if not peasõnadEraldatud:
                        lause_peasõnad.remove(alluv)

        if len(lause_peasõnad) <= 1:
            debug_info += pformat(lause_peasõnad)
            debug_info += "__ÜKS PEASÕNA__\n"
            tulemus += sisend.text + " "
            continue

        # Muudame kõik asesõnad vastavateks nimisõnadeks. Kasutades nimisõna mitmesust ja asesõna käänet.
        # Kasutades nii asesõna mitmesust kui käänet on võimalik, et tulemus pole see, mida ootame. Näiteks võib ainsuse asemel olla mitmus.
        # Semantilise info puudumise tõttu, saame iga tegusõna kohta asendada vaid ühe asesõna.
        kasutatud_tegusõnad = set()
        kustutatavad = []
        for i, element in enumerate(sõna_list):
            if element["pos"] == "P":
                if DEBUG:
                    debug_info += str(element) + '\n'
                if not (i > 2 and sõna_list[i - 1]["pos"] == "Z" and sõna_list[i - 2]["pos"] in {"S", "H"}
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
            debug_info += pformat(dict(siht_map))
            debug_info += pformat(lause_peasõnad)
            debug_info += "---------------------------------------------------\n"
            debug_info += str(sisend_sõne) + '\n'
            debug_info += "---------------------------------------------------\n"

        for sõna in lause_peasõnad:
            lause = moodustaLause(sobitaMalli(sõna, siht_map))
            tulemus += lause.strip() + '. '
        onLihtsustatud = True

    if onLihtsustatud:
        debug_info += "__LIHTSUSTATUD__\n"
    return (tulemus.strip(), debug_info)


def teeSõnaKoopia(sõna):
    uus_sõna = deepcopy(sõna)
    uus_sõna["indeks"] = -2
    return uus_sõna


def leiaOtseneSubjekt(verb, siht_map):
    for alluv in siht_map[verb["indeks"]]:
        if alluv["label"] == "@SUBJ":
            return alluv
    return None


def leiaTegusõnaSubjekt(verb, siht_map, sõna_list):
    subjekt = leiaOtseneSubjekt(verb, siht_map)
    if subjekt is not None:
        return teeSõnaKoopia(subjekt)
    if verb["target"] == -1:
        return None
    return leiaTegusõnaSubjekt(sõna_list[verb["target"]], siht_map, sõna_list)


def tagastaAlluvad(sõna, siht_map):
    sõna_list = []
    for alluv in siht_map[sõna["indeks"]]:
        if sõna["pos"] == "V" or alluv["pos"] != "V":
            sõna_list.append(alluv)
    return sõna_list


def sobitaMalli(sõna, siht_map):
    """
    Sõnapõhine lausemall

    :param sõna: Sõna, mille alluvate asukohti määratakse
    :param siht_map: Sõltuvustabel
    :return: Järjestatud sõna koos alluvatega
    """
    sõnade_list = []
    eel_list, järg_list = [], []
    for alluv in siht_map[sõna["indeks"]]:
        if sõna["pos"] == "V" or sõna["label"] in LAUSE_PEASÕNAD or alluv["pos"] != "V" or alluv["pos"] == "V" and \
                        alluv["label"] in ATRIBUUDID:
            if alluv["label"] == "@J" and not (">" in sõna["label"] and alluv["indeks"] > sõna["target"]):
                eel_list = sobitaMalli(alluv, siht_map) + eel_list
            else:
                eelListi = ">" in alluv["label"] or alluv["label"] in {"@SUBJ", "@FCV", "@NEG", "@ADVL"}
                järgListi = "<" in alluv["label"] or sõna["pos"] == "V" and alluv["label"] in {"@PRD", "@ADVL", "@OBJ"}
                järgListi2 = sõna["label"] == alluv["label"] and alluv["label"] in {"@SUBJ", "@PRD", "@ADVL", "@OBJ"}
                järgListi3 = sõna["label"] == "ROOT" and sõna["pos"] == alluv["pos"] and alluv["label"] in {"@SUBJ",
                                                                                                            "@PRD",
                                                                                                            "@ADVL",
                                                                                                            "@OBJ"}
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
    sisend = re.sub('\\\\', '', sisend)  # Üleliigsete kaldkriipsude eemaldamine
    sisend = re.sub('\n', ' ', sisend)
    sisend = re.sub('[“”„«»]', '"', sisend)  # jutumärkide ühtlustamine
    #  sulgude ühtlustamine
    sisend = re.sub('[\[{]', '(', sisend)
    sisend = re.sub('[\]}]', ')', sisend)
    return sisend


if len(sys.argv) > 2 and sys.argv[2] == "arg":
    result = lihtsusta(sys.argv[1])
    print(result[1])
    print('----', result[0])
