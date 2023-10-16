#!/usr/bin/env python3

import sys
from lxml import etree

for fpath in sys.argv[1:]:
	with open(fpath, encoding="utf-8") as _file:
		doc = etree.XML(_file.read().encode("utf-8"))

