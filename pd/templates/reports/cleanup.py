#/usr/bin/env python

import os
import tidy
import re

options = dict(indent=1, tidy_mark=0, char_encoding='utf8')

css = open('../reports_source/act_files/598663115-tiler_view.css', 'r').read()

for fname in os.listdir('.'):
    if '.html' in fname:
        f = open('../reports_source/' + fname, 'r')
        data = str(f.read())
        f.close()

        data = re.sub('<link rel=stylesheet href=".*?\.css" type="text/css">', '', data, re.I)
        data = re.sub('</head>', '<style>%s </style></head>' % css, data, re.I)

        print data[:1024]

        f = open(fname, 'w')
        f.write(str(tidy.parseString(data, **options)))
        f.close()
