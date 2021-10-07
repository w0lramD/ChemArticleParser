from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union, List

from .table import Table
from .paragraph import Paragraph, Sentence


class ArticleElementType(Enum):
    SECTION_ID = 1
    SECTION_TITLE = 2
    PARAGRAPH = 3
    TABLE = 4


@dataclass
class ArticleElement:
    type: ArticleElementType
    content: Union[Paragraph, Table, str]

    def __post_init__(self):
        if self.type == ArticleElementType.PARAGRAPH and isinstance(self.content, str) and len(self.content) > 0:
            self.content = Paragraph(text=self.content)


@dataclass
class ArticleComponentCheck:
    abstract: Optional[bool] = True
    sections: Optional[bool] = True


class Article:
    def __init__(self,
                 doi: Optional[str] = None,
                 title: Optional[Union[Sentence, str]] = None,
                 abstract: Optional[Union[Paragraph, str, List[str]]] = None,
                 sections: Optional[List[ArticleElement]] = None):

        self._doi = doi
        self._title = title
        self._abstract = abstract
        self._sections = sections if sections else list()
        self._post_init()

    def _post_init(self):
        if self._title and isinstance(self._title, str):
            self._title = Sentence(text=self._title)
        if self._abstract:
            if isinstance(self._abstract, str):
                self._abstract = Paragraph(self._abstract)
            elif isinstance(self._abstract, list) and isinstance(self._abstract[0], str):
                paras = list()
                for para in self._abstract:
                    para = para.strip()
                    if not para.endswith('.'):
                        para += f'.'
                    paras.append(para)
                self._abstract = Paragraph(' '.join(paras))

    @property
    def doi(self):
        return self._doi

    @property
    def title(self):
        return self._title

    @property
    def abstract(self):
        return self._abstract

    @property
    def sections(self):
        return self._sections

    @doi.setter
    def doi(self, x: str):
        self._doi = x

    @title.setter
    def title(self, x: Union[str, Sentence]):
        self._title = x if isinstance(x, Sentence) else Sentence(x)

    @abstract.setter
    def abstract(self, x: Union[Paragraph, str, List[str]]):
        if isinstance(x, str):
            self._abstract = Paragraph(x)
        elif isinstance(x, list) and isinstance(x[0], str):
            paras = list()
            for para in x:
                para = para.strip()
                if not para.endswith('.'):
                    para += '.'
                paras.append(para)
            self._abstract = Paragraph(' '.join(paras))
        else:
            self._abstract = x

    @sections.setter
    def sections(self, x: ArticleElement):
        self._sections = x

    def get_sentences_and_tokens(self, include_title=False):
        sent_list = list()
        tokens_list = list()
        if include_title:
            sent_list.append(self.title.text)
            tokens_list.append(self.title.tokens)

        sent_list += [sent.text for sent in self.abstract.sentences]
        tokens_list += [sent.tokens for sent in self.abstract.sentences]

        for section in self._sections:
            if section.type != ArticleElementType.PARAGRAPH:
                continue
            sent_list += [sent.text for sent in section.content.sentences]
            tokens_list += [sent.tokens for sent in section.content.sentences]
        return sent_list, tokens_list
