import regex
import re
import random
import numpy as np
import torch
import os
from chemdataextractor.doc import Paragraph


def format_text(text):

    # deal with interpuncts
    interpunct = r'[\u00B7\u02D1\u0387\u05BC\u16EB\u2022\u2027\u2218\u2219\u22C5\u23FA' \
                 r'\u25CF\u25E6\u26AB\u2981\u2E30\u2E31\u2E33\u30FB\uA78F\uFF65]'
    text = re.sub(interpunct, ' ', text)

    # deal with bullets
    bullets = r'[\u2022\u2023\u2043\u204C\u204D\u2219\u25CB\u25D8\u25E6' \
              r'\u2619\u2765\u2767\u29BE\u29BF]'
    text = re.sub(bullets, ' ', text)

    # deal with white spaces and \n
    text = regex.sub(r'[\p{Z}]', ' ', text)
    text = re.sub(r'([ \t]+)?[\r\n]([ \t]+)?', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'([ ]{2,})', ' ', text)

    # deal with "/"
    text = re.sub(r'[ ]?/[ ]?', '/', text)

    # deal with dash/hyphen
    text = regex.sub(r'[\p{Pd}]', '-', text)
    text = regex.sub(r'[\u2212\uf8ff\uf8fe\ue5f8]', '-', text)

    # deal with repeated comma and period
    text = re.sub(r'[.]+( *[,.])+', r'.', text)

    # deal with in-sentence references
    text = re.sub(r' *\[[0-9-, ]+][,-]*', r'', text)
    # deal with after-sentence references
    text = regex.sub(r'([A-Za-zα-ωΑ-Ω\p{Pe}\'"\u2018-\u201d]+[\d-]*)([.])( |[\d]+)([-, ]*[\d]*)*'
                     r'([ ]+[A-Z\dα-ωΑ-Ω\p{Ps}\'"\u2018-\u201d]|$)', r'\g<1>\g<2>\g<5>', text)

    text = text.strip()
    return text


def format_space(text):
    # deal with white spaces and \n
    text = regex.sub(r'[\p{Z}]', ' ', text)
    text = re.sub(r'([ ]{2,})', ' ', text)
    text = re.sub(r'([ \t]+)?[\r\n]([ \t]+)?', '\n', text)
    text = re.sub(r'\n+', ' ', text)
    text = text.strip()
    return text


def break_number_unit(text, unit_list):
    units_pattern = '|'.join(unit_list)
    text = re.sub(rf'([0-9])({units_pattern})', r'\g<1> \g<2>', text)
    return text


def entity_sent_span_conversion(paragraph, spans):
    para = Paragraph(paragraph)
    sent_spans = [(sent.start, sent.end) for sent in para]

    sent_entity_spans = list()
    para_spans = list()
    for span in spans:
        for sent_span in sent_spans:
            if sent_span[0] <= span[0] < sent_span[1]:
                candidate_sent_span = sent_span
                if candidate_sent_span not in sent_entity_spans:
                    sent_entity_spans.append(candidate_sent_span)
    para_spans += [(sent_span[0], sent_span[1]) for sent_span in sent_entity_spans]

    return para_spans


def separate_sentences(paragraph):
    tokens_list = list()
    sent_list = list()
    para = Paragraph(paragraph)
    for sent in para:
        tokens = [tk.text for tk in sent.tokens]
        tokens_list.append(tokens)
        sent_list.append(sent.text)
    return sent_list, tokens_list


def seed_everything(seed=42):
    """"
    Seed everything.
    """   
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True


def convert_cde_paragraph_to_sentences(para: Paragraph):
    sents = list()
    sent_ranges = list()
    for sent in para:
        sents.append(sent.text)
        sent_ranges.append((sent.start, sent.end))
    return sents, sent_ranges


def substring_mapping(text: str, mapping_dict: dict):
    rep = dict((re.escape(k), v) for k, v in mapping_dict.items())
    pattern = re.compile("|".join(rep.keys()))
    text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
    return text


# Function to sort the list of tuples by the second item
def sort_tuple_by_first_element(tup):
    # reverse = None (Sorts in Ascending order)
    # key is set to sort using second element of
    # sublist lambda has been used
    tup.sort(key=lambda x: x[0])
    return tup
