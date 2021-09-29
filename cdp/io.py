import os
import time
import itertools

from chemdataextractor.doc import Paragraph
from typing import Optional, List, Tuple
from .article import Article, ArticleElementType
from .table import Table, set_table_style
from .constants import *

try:
    import pyautogui
    import shutil
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import NoSuchElementException
except KeyError:
    pass

from bs4 import BeautifulSoup, Tag

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def scroll_down(driver_var, value):
    driver_var.execute_script("window.scrollBy(0," + str(value) + ")")


# Scroll down the page
def scroll_down_page(driver, n_max_try=100):

    old_page = driver.page_source
    for _ in range(n_max_try):
        for i in range(2):
            scroll_down(driver, 500)
            time.sleep(0.1)
        new_page = driver.page_source
        if new_page != old_page:
            old_page = new_page
        else:
            break
    return True


def every_downloads_chrome(driver):
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = document.querySelector('downloads-manager')
            .shadowRoot.getElementById('downloadsList').items;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def download_article_windows(doi, download_path, driver_path=None):

    article_url = 'https://doi.org/' + doi
    driver = webdriver.Chrome(executable_path=driver_path)

    driver.get(article_url)
    scroll_down_page(driver)

    if doi.startswith('10.1039'):
        try:
            driver.find_element_by_link_text('Article HTML').click()
            scroll_down_page(driver)
        except NoSuchElementException:
            pass

    pyautogui.hotkey('ctrl', 's')

    time.sleep(1)

    char_map = CHAR_TO_HTML_LBS

    file_name = ''.join(list(map(lambda x: char_map[x] if x in char_map.keys() else x, doi))) + '.html'
    save_path = os.path.join(download_path, file_name)
    save_path = os.path.abspath(os.path.normpath(save_path))

    if os.path.isfile(save_path):
        os.remove(save_path)
    if os.path.isdir(save_path.replace('.html', '_files')):
        shutil.rmtree(save_path.replace('.html', '_files'))
    pyautogui.write(save_path)
    pyautogui.hotkey('enter')
    time.sleep(0.1)

    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.1)
    driver.switch_to.window(driver.window_handles[1])
    _ = WebDriverWait(driver, 120, 1).until(every_downloads_chrome)
    time.sleep(0.1)

    driver.quit()


def set_html_style(root: Tag):
    soup = BeautifulSoup()
    style = soup.new_tag('style')
    root.insert(len(root), style)
    style_string = \
        """
        head {
          width: 85%;
          margin:auto auto;
        }
        
        body {
          width: 85%;
          margin:auto auto;
        }
        
        div {
          width: 100%;
          margin:auto auto;
        }
        
        p {
          text-align: justify;
          text-justify: inter-word;
        }
        
        .polymer {
        background-color: lightblue;
        color: black;
        } 
        """
    style.insert(0, style_string)
    return root


def save_html_results(save_file, article, valid_sent_ids=None, named_spans=None):
    if valid_sent_ids is None:
        valid_sent_ids = list()
    if named_spans is None:
        named_spans = list()

    soup = BeautifulSoup()
    head = soup.new_tag('head')
    soup.insert(0, head)
    title = soup.new_tag('title')
    head.insert(0, title)
    title.insert(0, article.title)

    set_html_style(head)
    set_table_style(head)

    viewport_meta = Tag(
        builder=soup.builder,
        name='meta',
        attrs={'name': "viewport", 'content': "width=device-width, initial-scale=1"}
    )
    head.insert(len(head), viewport_meta)

    title = soup.new_tag('h1')
    head.insert(len(head), title)
    title.insert(0, article.title)
    doi = soup.new_tag('p')
    head.insert(len(head), doi)
    doi.insert(0, f'doi:')
    doi_link = soup.new_tag('a', href=f'https://www.doi.org/{article.doi}')
    doi_link.insert(0, f'{article.doi}')
    doi.insert(len(doi), doi_link)

    body = soup.new_tag('body')
    soup.insert(len(soup), body)

    result_div = soup.new_tag('div', id='results')
    body.insert(len(body), result_div)
    result_title = soup.new_tag('h2')
    result_div.insert(len(result_div), result_title)
    result_title.insert(0, 'results')
    result_list = soup.new_tag('ol')
    result_div.insert(len(result_div), result_list)

    sents, _ = article.get_sentences()
    for idx in valid_sent_ids:
        result_p = soup.new_tag('li')
        result_list.insert(len(result_list), result_p)
        result_p.insert(0, sents[idx])
        result_link = soup.new_tag('a', href=f'#result{idx}')
        result_p.insert(len(result_p), result_link)
        result_link.insert(0, '[link]')

    body.insert(len(body), soup.new_tag('hr'))

    abs_div = soup.new_tag('div', id='abstract')
    body.insert(len(body), abs_div)

    sent_idx = 0
    if article.abstract:
        abs_title = soup.new_tag('h2')
        abs_div.insert(0, abs_title)
        abs_title.insert(0, 'Abstract')
        if isinstance(article.abstract, str):
            abstract = soup.new_tag('p')
            abs_div.insert(len(abs_div), abstract)
            abs_para = Paragraph(article.abstract)
            for sent in abs_para:
                sent_span = soup.new_tag('span')
                abstract.insert(len(abstract), sent_span)

                if named_spans:
                    if not named_spans[sent_idx]:
                        txt = sent.text
                    else:
                        spans = list(named_spans[sent_idx].keys())
                        txt = html_mark_spans(sent.text, spans, 'polymer')
                else:
                    txt = sent.text

                if sent_idx in valid_sent_ids:
                    sent_span['id'] = f'result{sent_idx}'
                    highlight = soup.new_tag('mark')
                    sent_span.insert(0, highlight)
                    highlight.insert(0, txt)
                else:
                    sent_span.insert(0, txt)
                sent_idx += 1
        elif isinstance(article.abstract, list):
            for abs_para in article.abstract:
                abstract = soup.new_tag('p')
                abs_div.insert(len(abs_div), abstract)
                abs_para = Paragraph(abs_para)
                for sent in abs_para:
                    sent_span = soup.new_tag('span')
                    abstract.insert(len(abstract), sent_span)

                    if named_spans:
                        if not named_spans[sent_idx]:
                            txt = sent.text
                        else:
                            spans = list(named_spans[sent_idx].keys())
                            txt = html_mark_spans(sent.text, spans, 'polymer')
                    else:
                        txt = sent.text

                    if sent_idx in valid_sent_ids:
                        sent_span['id'] = f'result{sent_idx}'
                        highlight = soup.new_tag('mark')
                        sent_span.insert(0, highlight)
                        highlight.insert(0, txt)
                    else:
                        sent_span.insert(0, txt)
                    sent_idx += 1

    sec_div = soup.new_tag('div', id='sections')
    body.insert(len(body), sec_div)
    for section in article.sections:
        if section.type == ArticleElementType.SECTION_TITLE:
            section_title = soup.new_tag('h2')
            sec_div.insert(len(sec_div), section_title)
            section_title.insert(0, section.content)
        elif section.type == ArticleElementType.PARAGRAPH:
            paragraph = soup.new_tag('p')
            sec_div.insert(len(sec_div), paragraph)

            para = Paragraph(section.content)
            for sent in para:
                sent_span = soup.new_tag('span')
                paragraph.insert(len(paragraph), sent_span)

                if named_spans:
                    if not named_spans[sent_idx]:
                        txt = sent.text
                    else:
                        spans = list(named_spans[sent_idx].keys())
                        txt = html_mark_spans(sent.text, spans, 'polymer')
                else:
                    txt = sent.text

                if sent_idx in valid_sent_ids:
                    sent_span['id'] = f'result{sent_idx}'
                    highlight = soup.new_tag('mark')
                    sent_span.insert(0, highlight)
                    highlight.insert(0, txt)
                else:
                    sent_span.insert(0, txt)
                sent_idx += 1
        elif section.type == ArticleElementType.TABLE:
            section.content.write_html(sec_div)

    soup_str = soup.prettify().replace('&lt;', '<').replace('&gt;', '>')
    with open(save_file, 'w', encoding='utf-8') as outfile:
        outfile.write(soup_str)


def html_mark_spans(text: str, spans: List[Tuple[int, int]], mark_class: Optional[str] = ''):
    """
    Wrap entity spans with HTML marker

    Parameters
    ----------
    text: input text string
    spans: input spans
    mark_class: the class of mark tag

    Returns
    -------
    Marked text
    """
    merged_spans = list(itertools.chain(*spans))
    merged_spans = [0] + merged_spans + [len(text)]
    splitted_str = [text[x:y] for x, y in zip(merged_spans, merged_spans[1:])]
    i = 1
    while i < len(splitted_str):
        splitted_str[i] = f'<mark class={mark_class}>{splitted_str[i]}</mark>'
        i += 2
    return ''.join(splitted_str)


def save_html_table(table: Table,
                    article: Optional[Article] = None,
                    save_name: Optional[str] = None):
    """
    save html-formatted tables
    This function should only be called for test.

    Parameters
    ----------
    table: parsed table elements,
    article: article where the table appears
    save_name: where to save the output file

    Returns
    -------
    None
    """
    soup = BeautifulSoup()
    head = soup.new_tag('head', style="width: 85%; margin:auto auto;")
    soup.insert(0, head)
    title = soup.new_tag('title')
    head.insert(0, title)
    if article:
        title.insert(0, article.title)
    else:
        title.insert(0, 'Test Table')

    set_table_style(head)

    html_body = soup.new_tag('body', style="width: 85%; margin:auto auto;")
    soup.insert(len(soup), html_body)

    table.write_html(html_body)

    file_name = save_name if save_name and save_name.lower().endswith('.html') else 'text.html'
    with open(file_name, 'w', encoding='utf-8') as outfile:
        outfile.write(soup.prettify())

    return None
