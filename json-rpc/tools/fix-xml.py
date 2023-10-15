#!/usr/bin/env python3

import sys

def fix_xml_file(fpath: str):
    with open(fpath) as _file :
        text = _file.read()
    text = text.replace('="<" ', '="&lt;" ')\
        .replace('=">" ', '="&gt;" ')\
        .replace('="<=" ', '="&lt;=" ')\
        .replace('=">=" ', '="&gt;=" ')
    with open(fpath, mode="w") as _file :
        _file.write(text)


for fpath in sys.argv[1:]:
    fix_xml_file(fpath)

