import logging
from dataclasses import dataclass
from typing import Optional, List

logger = logging.getLogger(__name__)


@dataclass
class Sentence:
    text: str
    start_idx: Optional[int] = None
    end_idx: Optional[int] = None
    anno: Optional[dict] = None

    def __post_init__(self):
        if self.start_idx is None:
            self.start_idx = 0
        if self.end_idx is None:
            self.end_idx = len(self.text)
        if self.anno is None:
            self.anno = dict()


class Paragraph:

    text: Optional[str] = None
    sentences: Optional[List["Sentence"]] = None
    anno: Optional[dict] = None

    def __init__(self,
                 text: Optional[str] = None,
                 sentences: Optional[List["Sentence"]] = None,
                 anno: Optional[dict] = None):
        self.text = text
        self.sentences = sentences
        self.anno = anno if anno is not None else dict()
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
        else:
            assert len(self.sentences) > 0, AttributeError("Assigning empty list to `sentences` is not allowed")

            start_idx = 0
            self.text = ' ' * (self.sentences[-1].end_idx + 1)
            for sent in self.sentences:
                assert sent.end_idx >= sent.start_idx >= start_idx, ValueError('Sentences are overlapping!')
                start_idx = sent.end_idx
                self.text[sent.start_idx: sent.end_idx] = sent.text

        sent_idx = 0
        for char_idx in range(len(self.text)):
            if self.sentences[sent_idx].start_idx <= char_idx < self.sentences[sent_idx].end_idx:
                self.char_idx_to_sent_idx[char_idx] = sent_idx
            elif char_idx == self.sentences[sent_idx].end_idx:
                sent_idx += 1

        self.align_anno()

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
        for (s, e), v in self.anno.items():
            sent_idx = self.char_idx_to_sent_idx[s]
            sent_s = s - self.sentences[sent_idx].start_idx
            sent_e = e - self.sentences[sent_idx].start_idx

            if sent_e > self.sentences[sent_idx].end_idx:
                logger.warning("Encountered multi-sentence annotation span, will skip")
                continue
            if (sent_s, sent_e) not in self.sentences[sent_idx].anno:
                self.sentences[sent_idx].anno[(sent_s, sent_e)] = v

        for sent in self.sentences:
            for (s, e), v in sent.anno.items():
                if (s+sent.start_idx, e+sent.end_idx) not in self.anno:
                    self.anno[(s+sent.start_idx, e+sent.start_idx)] = v

        return self

