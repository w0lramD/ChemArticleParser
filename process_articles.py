import os
import sys
import json
import torch
import logging
from datetime import datetime
from transformers import HfArgumentParser
from typing import Optional
from dataclasses import dataclass, field

from seqlbtoolkit.Text import substring_mapping
from seqlbtoolkit.IO import set_logging, logging_args

from cap.article_constr import (
    parse_html,
    parse_xml
)
from cap.constants import CHAR_TO_HTML_LBS
from cap.io import get_file_paths

logger = logging.getLogger(__name__)


@dataclass
class ArticleProcessingArgs:
    input_dir: str = field(
        metadata={"help": "The path to the HTML/XML article file."}
    )
    output_dir: Optional[str] = field(
        default='./output',
        metadata={"help": "The output folder where the validation results and relevant information is saved."},
    )
    log_file: Optional[str] = field(
        default=None,
        metadata={"help": "the directory of the log file. Set to '' to disable logging"}
    )
    skip_dois_path: Optional[str] = field(
        default='./data/seqcx-anno/exist-dois.json',
        metadata={'help': 'load existing dois (optional).'}
    )
    debug_mode: Optional[bool] = field(
        default=False, metadata={"help": "Debugging mode with fewer training data"}
    )


def process_articles(args: ArticleProcessingArgs):
    set_logging(args.log_file)
    logger.setLevel(logging.INFO)

    logging_args(args)

    logger.info("Getting article paths")
    file_list = get_file_paths(args.input_dir)
    logger.info(f"{len(file_list)} articles to be processed")

    if os.path.isfile(args.skip_dois_path):
        with open(args.skip_dois_path, 'r', encoding='utf-8') as f:
            dois_to_skip = json.load(f)
    else:
        if args.skip_dois_path:
            logger.warning("Argument 'skip_dois_path' is not empty but cannot be read.")
        dois_to_skip = list()

    logger.info("Processing articles")

    for file_idx, file_path in enumerate(file_list):

        file_path = os.path.normpath(file_path)
        logger.info(f"Processing {file_path}")

        try:
            if file_path.lower().endswith('html'):
                article, component_check = parse_html(file_path)
            elif file_path.lower().endswith('xml'):
                article, component_check = parse_xml(file_path)
            else:
                logger.error(f'Unsupported file type!')
                continue
        except Exception as e:
            logger.error(f"Failed to parse file. Error: {e}")
            continue

        try:
            if article.doi.lower() in dois_to_skip:
                continue
        except Exception as e:
            logger.error(f"Failed to get the dois. Error: {e}")
            continue

        try:
            # save parsed article
            save_dir = os.path.normpath(os.path.abspath(file_path)).split(os.sep)
            save_dir[-2] += '_processed'
            save_dir[-1] = f"{substring_mapping(article.doi, CHAR_TO_HTML_LBS)}.pt"
            save_path = os.path.normpath(os.path.join(args.output_dir, os.sep.join(save_dir[-2:])))
            if not os.path.isdir(os.path.split(save_path)[0]):
                os.makedirs(os.path.split(save_path)[0])
            torch.save(article, save_path)

        except Exception as e:
            logger.error(f"Failed to save results. Error: {e}")
            continue

        if args.debug_mode and file_idx >= 10:
            break

    logger.info('Program finished.')


if __name__ == '__main__':
    _time = datetime.now().strftime("%m.%d.%y-%H.%M")
    _current_file_name = os.path.basename(__file__)
    if _current_file_name.endswith('.py'):
        _current_file_name = _current_file_name[:-3]

    # --- set up arguments ---
    parser = HfArgumentParser(ArticleProcessingArgs)
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

    process_articles(args=article_args)
