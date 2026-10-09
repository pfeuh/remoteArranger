#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import unicodedata

def to_camel_case(s):
    # v 1.2 20260818 - Utilisation d'unicodedata pour nettoyer les accents proprement sans compter les caractères un par un
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    
    words = re.findall(r'[a-zA-Z0-9]+', s)
    if not words: return ""
    return words[0].lower() + "".join(w.capitalize() for w in words[1:])