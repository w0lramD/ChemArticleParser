import copy
import logging
from dataclasses import dataclass
from seqlbtoolkit.Eval import Metric
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class Sentence:
    text: str
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    anno: Optional[dict] = None
    anno_groups: Optional[List[Metric]] = None

    def __post_init__(self):
        if self.start_idx is None:
            self.start_idx = 0
        if self.end_idx is None:
            self.end_idx = len(self.text)
        if self.anno is None:
            self.anno = dict()
        if self.anno_groups is None:
            self.anno_groups = list()


class Paragraph:
    def __init__(self,
                 text: Optional[str] = None,
                 sentences: Optional[List["Sentence"]] = None,
                 anno: Optional[dict] = None,
                 anno_groups: Optional[List[Metric]] = None):
        self.text = text
        self.sentences = sentences
        self.anno = anno if anno is not None else dict()
        self.anno_groups = anno_groups if anno_groups is not None else list()
        self.char_idx_to_sent_idx = dict()
        self._post_init()

    def _post_init(self):
        if self.sentences is None:
            sents = self.sentence_tokenize()
            self.sentences = list()

            s_idx = 0
            for sent in sents:
                self.sentences.append(Sentence(sent, s_idx, s_idx+len(sent)))
                s_idx += len(sent) + 1

            self.text = ' '.join(sents)

            self.update_sentence_anno()

        else:
            assert len(self.sentences) > 0, AttributeError("Assigning empty list to `sentences` is not allowed")

            start_idx = 0
            self.text = ' ' * (self.sentences[-1].end_idx + 1)
            for sent in self.sentences:
                assert sent.end_idx > sent.start_idx >= start_idx, ValueError('Sentences are overlapping!')
                start_idx = sent.end_idx
                self.text[sent.start_idx: sent.end_idx] = sent.text

            self.update_paragraph_anno()

        if not self.char_idx_to_sent_idx:
            self._get_char_idx_to_sent_idx()

    def _get_char_idx_to_sent_idx(self):
        sent_idx = 0
        for char_idx in range(len(self.text)):
            if self.sentences[sent_idx].start_idx <= char_idx < self.sentences[sent_idx].end_idx:
                self.char_idx_to_sent_idx[char_idx] = sent_idx
            elif char_idx == self.sentences[sent_idx].end_idx:
                sent_idx += 1

    def get_sentence_by_char_idx(self, char_idx: int):
        sent_idx = self.char_idx_to_sent_idx[char_idx]
        return self.sentences[sent_idx]

    # noinspection PyTypeChecker
    def sentence_tokenize(self):
        from chemdataextractor.doc import Paragraph
        para = Paragraph(self.text)

        sents = list()
        for sent in para.sentences:
            sents.append(sent.text)

        return sents

    def align_anno(self):
        """
        Align sentence and paragraph-level annotations
        """
        self.update_sentence_anno()
        self.update_paragraph_anno()
        return self

    def update_paragraph_anno(self, sent_idx: Optional[int] = None):
        if sent_idx is None:
            for sent in self.sentences:
                for (s, e), v in sent.anno.items():
                    if (s+sent.start_idx, e+sent.start_idx) not in self.anno:
                        self.anno[(s+sent.start_idx, e+sent.start_idx)] = v
        elif isinstance(sent_idx, int):
            sent = self.sentences[sent_idx]
            for (s, e), v in sent.anno.items():
                if (s + sent.start_idx, e + sent.start_idx) not in self.anno:
                    self.anno[(s + sent.start_idx, e + sent.start_idx)] = v
        else:
            raise ValueError(f'Unsupported index type: {type(sent_idx)}')

        return self

    def update_sentence_anno(self):
        if not self.char_idx_to_sent_idx:
            self._get_char_idx_to_sent_idx()

        for (s, e), v in self.anno.items():
            sent_idx = self.char_idx_to_sent_idx[s]
            sent_s = s - self.sentences[sent_idx].start_idx
            sent_e = e - self.sentences[sent_idx].start_idx

            if sent_e > self.sentences[sent_idx].end_idx:
                logger.warning("Encountered multi-sentence annotation span. Will split.")

                self.sentences[sent_idx].anno[(sent_s, self.sentences[sent_idx].end_idx)] = v
                self.sentences[sent_idx + 1].anno[(0, e - self.sentences[sent_idx + 1].start_idx)] = v
            if (sent_s, sent_e) not in self.sentences[sent_idx].anno:
                self.sentences[sent_idx].anno[(sent_s, sent_e)] = v
        return self

    def update_paragraph_anno_group(self, sent_idx: Optional[int] = None):
        """
        update paragraph annotation group
        """
        if sent_idx is None:
            anno_groups = list()
            for sent in self.sentences:
                if not sent.anno_groups:
                    continue
                for anno_group in sent.anno_groups:
                    para_anno_group = copy.deepcopy(anno_group)
                    for k in para_anno_group.keys():
                        if isinstance(para_anno_group[k], tuple) and len(para_anno_group[k]) == 2:
                            s, e = para_anno_group[k]
                            para_anno_group[k] = (s+sent.start_idx, e+sent.start_idx)
                        elif isinstance(para_anno_group[k], list) and len(para_anno_group[k]) > 0:
                            for i in range(len(para_anno_group[k])):
                                anno_pair = para_anno_group[k][i]
                                if isinstance(anno_pair, tuple) and len(anno_pair) == 2:
                                    s, e = anno_pair
                                    para_anno_group[k][i] = (s+sent.start_idx, e+sent.start_idx)
                        else:
                            pass
                    anno_groups.append(para_anno_group)
            self.anno_groups = anno_groups

        elif isinstance(sent_idx, int):

            sent = self.sentences[sent_idx]
            if not sent.anno_groups:
                return self
            anno_groups = list()
            for anno_group in sent.anno_groups:
                para_anno_group = copy.deepcopy(anno_group)
                for k in para_anno_group.keys():
                    if isinstance(para_anno_group[k], tuple) and len(para_anno_group[k]) == 2:
                        s, e = para_anno_group[k]
                        para_anno_group[k] = (s+sent.start_idx, e+sent.start_idx)
                anno_groups.append(para_anno_group)

            self.anno_groups += anno_groups
            self.anno_groups = list(set(self.anno_groups))

        else:
            raise ValueError(f'Unsupported index type: {type(sent_idx)}')

    def update_sentence_anno_group(self):
        raise NotImplementedError
