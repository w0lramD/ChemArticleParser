import regex
import textspan
import numpy as np
from chemdataextractor.nlp.tokenize import ChemWordTokenizer
from chemdataextractor.doc import Paragraph
from Src.Constants import *
from Src.Utils import sort_tuple_by_first_element

from typing import List
from seqlbtoolkit.Data import txt_to_token_span


def unit_detector(text, units):
    units_pattern = '|'.join(units)
    spans = regex.finditer('([ 0-9\p{Ps}\p{Pe}\'"\u2018-\u201d])(%s)'
                           '($|[ \p{Ps}\p{Pe}\'"\u2018-\u201d,.])' % units_pattern, text)
    detected_spans = [(m.span(2)[0], m.span(2)[1]) for m in spans]
    detected_spans = list(set(detected_spans))
    detected_spans = sort_tuple_by_first_element(detected_spans)

    return detected_spans


def term_detector(text, terms):
    terms_pattern = '|'.join(terms)
    spans = regex.finditer('(^|[ \p{Ps}\'"\u2018-\u201d])(%s)'
                           '($|[ \p{Ps}\p{Pe}\'"\u2018-\u201d,.])' % terms_pattern, text)
    detected_spans = [(m.span(2)[0], m.span(2)[1]) for m in spans]
    detected_spans = list(set(detected_spans))
    detected_spans = sort_tuple_by_first_element(detected_spans)

    return detected_spans


# def number_detector(text):
#     cwt = ChemWordTokenizer()
#     tokens = cwt.tokenize(text)
#     spans = cwt.span_tokenize(text)
#
#     detected_spans = list()
#     for i, (token, span) in enumerate(zip(tokens, spans)):
#         try:
#             _ = float(token)
#         except ValueError:
#             if not regex.findall(r"(^|[\p{Ps} ])[0-9]+[-][0-9]+([.]*$|[ \p{Ps}\p{Pe}])", token):
#                 continue
#         prev_tokens = ' '.join(tokens[i-3 if i-3 > 0 else 0: i]).lower().strip().replace('.', '')
#         element_keywords = 'figure|fig|table|tb|eq|equ|equation|section|sec|alg|algorithm|§|chapter|ch'
#         if i == 0 or not regex.findall(
#                 r'(^|[\p{Ps} ])(%s)([.]*$|[ \p{Ps}\p{Pe}])' % element_keywords, prev_tokens
#         ):
#             detected_spans.append(span)
#
#     detected_spans = sort_tuple_by_first_element(detected_spans)
#     return detected_spans


def number_detector(text):
    cwt = ChemWordTokenizer()
    tokens = cwt.tokenize(text)
    cde_text = ' '.join(tokens)

    spans = regex.finditer(r"(?:^|[\p{Ps} =<>]) *(-* *\d+(?:.\d+)*((?:-|±|,| |to|or|and)+\d+(?:.\d+)*)*)"
                           r"(?:[.]*$|[ \p{Ps}\p{Pe}])", cde_text)
    spans = [(m.span(1)[0], m.span(1)[1]) for m in spans]
    spans = list(set(spans))

    detected_spans = list()
    token_spans = txt_to_token_span(tokens, cde_text, spans)
    for span, token_span in zip(spans, token_spans):
        ts = token_span[0]
        prev_tokens = ' '.join(tokens[ts - 3 if ts - 3 > 0 else 0: ts]).lower().strip().replace('.', '')
        element_keywords = 'figure|fig|table|tb|eq|equ|equation|section|sec|alg|algorithm|§|chapter|ch'
        if ts == 0 or not regex.findall(
                r'(^|[\p{Ps} ])(%s)([.]*$|[ \p{Ps}\p{Pe}])' % element_keywords, prev_tokens
        ):
            detected_spans.append(span)

    detected_spans = [s[0] for s in textspan.align_spans(detected_spans, cde_text, text)]
    detected_spans = sort_tuple_by_first_element(detected_spans)
    return detected_spans


def validate_unit_spans(unit_spans, number_spans):
    # check if unit_spans are valid
    valid_spans = list()
    for unit_span in unit_spans:
        s = unit_span[0]
        for number_span in number_spans:
            ne = number_span[1]
            if abs(s - ne) <= 5:
                valid_spans.append(unit_span)
                break
    return valid_spans


def validate_term_spans(text, term_spans, number_spans, all_unit_spans):
    if (not term_spans) or (not number_spans) or (not all_unit_spans):
        return []

    para = Paragraph(text)
    sent_ranges = [(sent.start, sent.end) for sent in para]

    # check if term_spans are valid
    valid_spans = list()
    for term_span in term_spans:
        number_valid_flag = False
        unit_valid_flag = False
        s = term_span[0]
        e = term_span[1]
        sent_range = (0, 1)
        # check which sentence the target span belongs to.
        for sent_range in sent_ranges:
            if sent_range[0] <= s < sent_range[1]:
                break
        # make sure Tc refers to the ceiling temperature
        if text[s-1 if s > 0 else 0: e+1 if e+1 < len(text) else len(text)] == '(Tc)':
            if 'ceiling' not in text[sent_range[0]: sent_range[1]]:
                continue
        for number_span in number_spans:
            ns = number_span[0]
            if sent_range[0] <= ns < sent_range[1]:
                number_valid_flag = True
                break
        for unit_span in all_unit_spans:
            us = unit_span[0]
            if sent_range[0] <= us < sent_range[1] and number_spans[0][1] < us:
                unit_valid_flag = True
                break
        if number_valid_flag and unit_valid_flag:
            valid_spans.append(term_span)
    return valid_spans


def check_text_valid_heuristic(text: str):

    unit_spans = unit_detector(text, ENERGY_UNITS)
    general_unit_spans = unit_detector(text, TEMPERATURE_UNITS)
    all_unit_spans = sort_tuple_by_first_element(list(set(unit_spans + general_unit_spans)))

    term_spans = term_detector(text, ENERGY_TERMS+TEMPERATURE_TERMS)
    number_spans = number_detector(text)

    # check if unit_spans are valid
    valid_spans = validate_unit_spans(unit_spans=unit_spans, number_spans=number_spans)

    valid_spans += validate_term_spans(
        text=text,
        term_spans=term_spans,
        number_spans=number_spans,
        all_unit_spans=all_unit_spans
    )

    if valid_spans != [] and term_spans != []:
        return True
    else:
        return False


def locate_valid_sents_heuristic(sents: List[str]):
    valid_ids = list()
    check_results = list()
    for idx, sent in enumerate(sents):
        if check_text_valid_heuristic(sent):
            valid_ids.append(idx)
            check_results.append(True)
        else:
            check_results.append(False)
    return valid_ids, check_results


def get_entity_values(sent: str):
    entropy_unit_spans = unit_detector(sent, ENTROPY_UNITS)
    enthalpy_unit_spans = unit_detector(sent, ENTHALPY_UNITS)
    entropy_span_start_pos = [s[0] for s in entropy_unit_spans]
    enthalpy_unit_spans = [s for s in enthalpy_unit_spans if s[0] not in entropy_span_start_pos]

    temperature_unit_spans = unit_detector(sent, TEMPERATURE_UNITS)
    number_spans = number_detector(sent)

    tc_values = list()
    for tu_span in temperature_unit_spans:
        us, ue = tu_span
        for number_span in number_spans:
            ns, ne = number_span
            if np.abs(us - ne) < 3:
                tc_values.append(sent[ns: ue])

    enthalpy_values = list()
    entropy_values = list()
    for eu_span in entropy_unit_spans:
        es, ee = eu_span
        for number_span in number_spans:
            ns, ne = number_span
            if np.abs(es - ne) < 3:
                entropy_values.append(sent[ns: ee])
    for eu_span in enthalpy_unit_spans:
        es, ee = eu_span
        for number_span in number_spans:
            ns, ne = number_span
            if np.abs(es - ne) < 3:
                enthalpy_values.append(sent[ns: ee])

    return tc_values, entropy_values, enthalpy_values


def append_entropy_value(info_list, entropy_values, sent):
    for v in entropy_values:
        info_list.append({
            'Tc': '',
            'ΔH': '',
            'ΔS': v,
            'sentence': sent,
        })


def append_enthalpy_value(info_list, enthalpy_values, sent):
    for v in enthalpy_values:
        info_list.append({
            'Tc': '',
            'ΔH': v,
            'ΔS': '',
            'sentence': sent,
        })


def append_tc_value(info_list, ct_values, sent):
    for v in ct_values:
        info_list.append({
            'Tc': v,
            'ΔH': '',
            'ΔS': '',
            'sentence': sent,
        })


def group_rop_properties(sent: str):
    tc_values, entropy_values, enthalpy_values = get_entity_values(sent)
    info_list = list()

    if len(tc_values) == 1 and len(enthalpy_values) == 1 and len(entropy_values) == 1:
        info_list.append({
            'Tc': tc_values[0],
            'ΔH': enthalpy_values[0],
            'ΔS': entropy_values[0],
            'sentence': sent,
        })
    elif len(tc_values) == 1 and len(enthalpy_values) == 1:
        info_list.append({
            'Tc': tc_values[0],
            'ΔH': enthalpy_values[0],
            'ΔS': '',
            'sentence': sent,
        })
        append_entropy_value(info_list, entropy_values, sent)
    elif len(tc_values) == 1 and len(entropy_values) == 1:
        info_list.append({
            'Tc': tc_values[0],
            'ΔH': '',
            'ΔS': entropy_values[0],
            'sentence': sent,
        })
        append_enthalpy_value(info_list, entropy_values, sent)
    elif len(enthalpy_values) == 1 and len(entropy_values) == 1:
        info_list.append({
            'Tc': '',
            'ΔH': enthalpy_values[0],
            'ΔS': entropy_values[0],
            'sentence': sent,
        })
        append_tc_value(info_list, tc_values, sent)
    else:
        append_tc_value(info_list, tc_values, sent)
        append_enthalpy_value(info_list, enthalpy_values, sent)
        append_entropy_value(info_list, entropy_values, sent)

    return info_list
