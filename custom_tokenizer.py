import nltk.data
import re
from copy import copy
from estnltk import Text
from estnltk.tokenizers import word_tokenizer
from nltk.tokenize.api import StringTokenizer


class CustomWordTokenizer(StringTokenizer):
    def tokenize(self, s):
        return word_tokenize(s)[0]

    def span_tokenize(self, s):
        return word_tokenize(s)[1]


class CustomSentenceTokenizer(StringTokenizer):
    def __init__(self):
        self.tok = nltk.data.load('tokenizers/punkt/estonian.pickle')

    def tokenize(self, s):
        return sent_tokenize(s, self.tok)[0]

    def span_tokenize(self, s):
        return sent_tokenize(s, self.tok)[1]


def word_tokenize(text):
    tokens, spans = word_tokenizer.word_tokenize(text)
    tokens_copy, spans_copy = copy(tokens), copy(spans)
    algus = 0
    sulgusi = 0
    token_count = 0
    jutumärkides = False
    uuendus = False
    for i, token in enumerate(tokens_copy):
        if '"' in token and sulgusi == 0:
            jutumärkides = not jutumärkides
            if jutumärkides:
                algus = i
            else:
                uuendus = True
        elif '(' in token and not jutumärkides:
            sulgusi += 1
            if sulgusi == 1:
                algus = i
        elif ')' in token and not jutumärkides and not sulgusi <= 0:
            sulgusi -= 1
            if sulgusi == 0:
                uuendus = True
        if uuendus:
            span = (spans_copy[algus][0], spans_copy[i][1])
            spans[algus - token_count + 1:i - token_count] = [span]
            tokens[algus - token_count + 1:i - token_count] = [text[span[0]:span[1]]]
            token_count = len(tokens_copy) - len(tokens)
            uuendus = False
    return tokens, spans


def sent_tokenize(text, tok):
    tokens = tok.tokenize(text)
    spans = list(tok.span_tokenize(text))
    tokens_copy, spans_copy = copy(tokens), copy(spans)
    algus = 0
    otsekõne = False
    token_count = 0
    for i, token in enumerate(tokens_copy):
        if re.match('.?"', token) and not re.match('.*".?', token):
            otsekõne = True
            algus = i
        elif re.match('.*".?', token) and otsekõne:
            span = (spans_copy[algus][0], spans_copy[i][1])
            spans[algus - token_count:i + 1 - token_count] = [span]
            tokens[algus - token_count:i + 1 - token_count] = [text[span[0]:span[1]]]
            token_count = len(tokens_copy) - len(tokens)
            otsekõne = False
    return tokens, spans
