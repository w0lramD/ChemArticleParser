# chem-doc-parsing
Convert HTML/XML Chemistry/Material Science articles into plain text.

---

## Requirement

See `requirements.txt`.

## Supported publishers:

- RSC (HTML, w/ table)
- Springer (HTML, w/ table)
- Nature (HTML, w/o table)
- Wiley (HTML, w/ table)
- AIP (HTML, w/o table)
- ACS (HTML & XML, w/ table)
- Elsevier (HTML & XML, w/ table)
- AAAS (Science) (HTML, w/o table)

## Example

To parse HTML files, run the following code:
```shell
python parse_articles.py --input_dir </path/to/html/files> --parse_html
```

Add `--parse_xml` to the argument list to enable xml parsing.
