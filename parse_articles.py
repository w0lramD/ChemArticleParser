import os
import sys
import glob
import torch
import logging
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
from dataclasses import dataclass, field
from transformers import HfArgumentParser

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

from seqlbtoolkit.Text import substring_mapping
from seqlbtoolkit.IO import set_logging, logging_args

from cdp.article_constr import (
    ArticleFunctions,
    search_html_doi_publisher,
    search_xml_doi_publisher
)
from cdp.constants import CHAR_TO_HTML_LBS

logger = logging.getLogger(__name__)


@dataclass
class ArticleParsingArgs:
    input_dir: str = field(
        metadata={"help": "where the inputs are stored"},
    )
    log_file: Optional[str] = field(
        default=None,
        metadata={"help": "the directory of the log file. Set to '' to disable logging"}
    )
    parse_html: Optional[bool] = field(
        default=False,
        metadata={"help": "parse html articles"}
    )
    parse_xml: Optional[bool] = field(
        default=False,
        metadata={"help": "parse xml articles"}
    )


def parse_articles(args):
    set_logging(args.log_file)
    logger.setLevel(logging.INFO)

    logging_args(args)

    input_loc = os.path.normpath(args.input_dir)

    if args.parse_html:

        logger.info(f'Searching HTML files in {input_loc}')
        html_file_paths = glob.glob(os.path.join(input_loc, "*.html"))
        html_file_paths.sort()
        logger.info(f'Found {len(html_file_paths)} HTML articles')

        logger.info('Parsing HTML files...')

        for file_path in tqdm(html_file_paths):
            file_path = os.path.normpath(file_path)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
            except Exception as e:
                logger.warning(f'Failed to read {file_path}: {e}')
            soup = BeautifulSoup(contents, 'lxml')

            # get publisher and doi
            try:
                doi, publisher = search_html_doi_publisher(soup)
            except Exception as e:
                logger.warning(f'File {file_path} is from unsupported publishers. Error message: {e}')
                continue

            if publisher == 'elsevier':
                # allow illegal nested <p>
                soup = BeautifulSoup(contents, 'html.parser')

            article_construct_func = getattr(ArticleFunctions, f'article_construct_html_{publisher}')

            try:
                article, component_check = article_construct_func(soup=soup, doi=doi)
            except Exception as e:
                logger.error(f'Encountered error {e} while parsing {file_path}')
                continue

            if not component_check.abstract:
                logger.warning(f'{publisher}: {file_path} does not have abstract!')
            if not component_check.sections:
                logger.warning(f'{publisher}: {file_path} does not have HTML sections!')

            if not (component_check.abstract or component_check.sections):
                continue

            save_dir = os.path.normpath(file_path).split(os.sep)
            save_dir[-2] += '_plain'
            save_dir[-1] = f"{substring_mapping(doi, CHAR_TO_HTML_LBS)}.pt"
            if not os.path.isdir(os.sep.join(save_dir[:-1])):
                os.mkdir(os.sep.join(save_dir[:-1]))
            torch.save(article, os.sep.join(save_dir))

    if args.parse_xml:

        logger.info(f'Searching XML files in {input_loc}')
        xml_file_paths = glob.glob(os.path.join(input_loc, "*.xml"))
        xml_file_paths.sort()
        logger.info(f'Found {len(xml_file_paths)} XML articles')

        logger.info('Parsing XML files...')
        for file_path in tqdm(xml_file_paths):
            file_path = os.path.normpath(file_path)

            tree = ET.parse(file_path)
            root = tree.getroot()

            # get the publisher
            try:
                doi, publisher = search_xml_doi_publisher(root)
            except Exception as e:
                logger.warning(f'File {file_path} is from unsupported publishers. Error message: {e}')
                continue

            article_construct_func = getattr(ArticleFunctions, f'article_construct_xml_{publisher}')

            try:
                article, component_check = article_construct_func(root=root, doi=doi)
            except Exception as e:
                logger.error(f'Encountered error {e} while parsing {file_path}')
                continue

            if not component_check.abstract:
                logger.warning(f'{publisher}: {file_path} does not have abstract!')
            if not component_check.sections:
                logger.warning(f'{publisher}: {file_path} does not have XML sections!')
                continue

            if not (component_check.abstract or component_check.sections):
                continue

            save_dir = os.path.normpath(file_path).split(os.sep)
            save_dir[-2] += '_plain'
            save_dir[-1] = f"{substring_mapping(doi, CHAR_TO_HTML_LBS)}.pt"
            if not os.path.isdir(os.sep.join(save_dir[:-1])):
                os.mkdir(os.sep.join(save_dir[:-1]))
            torch.save(article, os.sep.join(save_dir))

    logger.info('Program finished! Exiting...')


if __name__ == '__main__':
    _time = datetime.now().strftime("%m.%d.%y-%H.%M")
    _current_file_name = os.path.basename(__file__)
    if _current_file_name.endswith('.py'):
        _current_file_name = _current_file_name[:-3]

    # --- set up arguments ---
    parser = HfArgumentParser(ArticleParsingArgs)
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        article_args, = parser.parse_json_file(
            json_file=os.path.abspath(sys.argv[1])
        )
    else:
        article_args, = parser.parse_args_into_dataclasses()

    if article_args.log_file is None:
        article_args.log_file = os.path.join('logs', f'{_current_file_name}.{_time}.log')

    parse_articles(args=article_args)
