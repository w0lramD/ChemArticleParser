from enum import Enum
from dataclasses import dataclass
from typing import Optional, Union, List
from Src.Utils import separate_sentences
from Src.Table import Table


class ArticleElementType(Enum):
    SECTION_ID = 1
    SECTION_TITLE = 2
    PARAGRAPH = 3
    TABLE = 4


@dataclass
class ArticleElement:
    type: ArticleElementType
    content: Union[str, Table]


@dataclass
class ArticleComponentCheck:
    abstract: Optional[bool] = True
    sections: Optional[bool] = True


class Article:
    def __init__(self,
                 doi: Optional[str] = '',
                 title: Optional[str] = '',
                 abstract: Optional[Union[str, List[str]]] = '',
                 sections: Optional[List[ArticleElement]] = None):

        self._doi = doi
        self._title = title
        self._abstract = abstract
        self._sections = sections if sections else list()

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
    def doi(self, x):
        self._doi = x

    @title.setter
    def title(self, x):
        self._title = x

    @abstract.setter
    def abstract(self, x):
        self._abstract = x

    @sections.setter
    def sections(self, x):
        self._sections = x

    def get_sentences(self, include_title=False):
        sent_list = list()
        tokens_list = list()
        if include_title:
            sent_list += [self._title]
        if isinstance(self._abstract, str):
            sent, tokens = separate_sentences(self._abstract)
            sent_list += sent
            tokens_list += tokens
        elif isinstance(self._abstract, list):
            for abstr in self._abstract:
                sent, tokens = separate_sentences(abstr)
                sent_list += sent
                tokens_list += tokens
        for section in self._sections:
            if section.type != ArticleElementType.PARAGRAPH:
                continue
            sent, tokens = separate_sentences(section.content)
            sent_list += sent
            tokens_list += tokens
        return sent_list, tokens_list
