# -*- coding: utf-8 -*-

from unittest import TestCase

from ..templatetags import cstags

class TemplateTagsTestCase(TestCase):
    def test_unbreakable_space(self):
        str = u'Otestuje a doplní obsah knihy. Otestuje a doplní obsah knihy.'
        str_parsed = u'Otestuje a doplní obsah knihy. Otestuje a doplní obsah\xa0knihy.'
        self.assertEqual(str_parsed, cstags.typify(str))