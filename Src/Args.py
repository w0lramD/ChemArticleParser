import logging
from typing import Optional
from dataclasses import dataclass, field

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


@dataclass
class AutoValidationArgs:
    input_dir: str = field(
        metadata={"help": "The folder that contains articles to validate or a json file contains the file locations"}
    )
    output_dir: Optional[str] = field(
        default='./output',
        metadata={"help": "The output folder where the validation results and relevant information is saved."},
    )
    ner_model_dir: Optional[str] = field(
        default='./models/pet-mm-model', metadata={'help': 'ner model directory'}
    )
    sent_classifier_dir: Optional[str] = field(
        default='./models/biobert-classifier', metadata={'help': 'sentence classification model directory'}
    )
    batch_size: Optional[int] = field(
        default=None, metadata={'help': 'model inference batch size. Leave None for original batch size'}
    )
    dois_to_skip_file: Optional[str] = field(
        default='classification-data/exist-dois.json',
        metadata={'help': 'load existing dois (optional).'}
    )
    log_file: Optional[str] = field(
        default=None,
        metadata={"help": "the directory of the log file. Set to '' to disable logging"}
    )
    include_heuristic: Optional[bool] = field(
        default=False,
        metadata={"help": "whether to use heuristic rules to regularize prediction results"}
    )
    debug_mode: Optional[bool] = field(
        default=False, metadata={"help": "Debugging mode with fewer training data"}
    )
