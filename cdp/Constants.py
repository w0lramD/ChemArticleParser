SUPPORTED_HTML_PUBLISHERS = ['rsc', 'springer', 'nature', 'wiley', 'aip', 'acs', 'elsevier', 'aaas']
SUPPORTED_XML_PUBLISHERS = ['acs', 'elsevier']

FILENAME_CHARACTERS_TO_LABELS = {
    '/': '&sl;',
    '\\': '&bs;',
    '?': '&qm;',
    '*': '&st;',
    ':': '&cl;',
    '|': '&vb;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&apos;'
}

HTML_CHARACTERS_TO_LABELS = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&apos;'
}

LABELS_TO_SPECIAL_CHARACTERS = {
    '^sl': '/',
    '@': '/',
    '^bs': '\\',
    '^qm': '?',
    '^st': '*',
    '^cl': ':',
    '^vb': '|',
    '^lt': '<',
    '^gt': '>',
    '^dq': '"',
    '^sq': '\'',
    '&sl;': '/',
    '&bs;': '\\',
    '&qm;': '?',
    '&st;': '*',
    '&cl;': ':',
    '&vb;': '|',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&apos;': '\'',
    '&amp;': '&'
}

HTML_LBS_TO_CHAR = {
    '&sl;': '/',
    '&bs;': '\\',
    '&qm;': '?',
    '&st;': '*',
    '&cl;': ':',
    '&vb;': '|',
    '&lt;': '<',
    '&gt;': '>',
    '&quot;': '"',
    '&apos;': '\'',
    '&amp;': '&'
}
