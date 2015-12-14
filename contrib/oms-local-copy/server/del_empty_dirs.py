#! /usr/bin/env python
# -*- coding: utf-8 -*-

# del_empty_dirs.py

# Удалить каталог, если он пустой. И верхний каталог, если пустой. И т.д.
# Принимает имена каталогов на sys.stdin

import sys, os

for line in sys.stdin:
    try:
        os.removedirs(line.rstrip())
    except OSError:
        pass
