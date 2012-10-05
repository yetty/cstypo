import re


class TxtParser(object):
    '''
    Class to apply Czech typography rules to input text.
    Most of regular expressions are from Texy!

    http://github.com/dg/texy/blob/master/Texy/modules/TexyTypographyModule.php

    '''

    text = ''
    positions = {}
    extracted = {}

    def __init__(self, text=''):
        '''
        Create instance of TxtParser, save input.

        >>> myparser = TxtParser('This is my input')
        >>> print myparser.text
        This is my input

        You must not to provide input.
        >>> myparser = TxtParser()
        >>> myparser.text == ''
        True

        '''

        self.text = text.decode('string-escape').decode('utf-8')
        self.positions = {}
        self.extracted = {}

    def parse(self):
        '''
        Runs all methods to parse input text.
        '''

        text = self.text
        self.positions = {}     # for multiple parsing

        for method in dir(self):
            if 'parse_' in method:
                callable = getattr(self, method)
                text = callable(text)

        return text

    def sub(self, pattern, repl, s, extract=False):
        '''
        Method for replacing by pattern and saving
        the difference.

        >>> import re
        >>> parser = TxtParser()
        >>> pattern = re.compile(ur'\.{3}')
        >>> parser.sub(pattern, '?', 'First... Second...')
        'First? Second?'
        >>> parser.positions
        {5: -2, 13: -2}
        '''

        while True:
            pos = pattern.search(s)
            if not pos:
                break

            start = pos.start()
            length = len(s)
            s = pattern.sub(repl, s, 1)
            diff = len(s) - length

            if not start in self.positions:
                self.positions[start] = diff
            else:
                self.positions[start] += diff

            if extract:
                self.extracted[start] = pos.group()

            if self.positions[start] == 0:
                del self.positions[start]

        return s

    def parse_ellipsis(self, text):
        '''
        Replace three dots by ellipsis.

        >>> parser = TxtParser()
        >>> parser.parse_ellipsis('Simple...')
        u'Simple\u2026'

        >>> parser.parse_ellipsis('More complex... Test. With some dots.')
        u'More complex\u2026 Test. With some dots.'

        Four dots are equal to three -> ellipsis.
        >>> parser.parse_ellipsis('What about four dots....?')
        u'What about four dots\u2026?'
        '''

        pattern = re.compile(ur'''
                    (?<![.\u2026])      # no ellipsis before
                    \.{3,4}             # three or four dots
                    (?![.\u2026])       # no ellipsis after
                 ''', re.M | re.U | re.X)
        return self.sub(pattern, u'\u2026', text)

    def parse_en_dash(self, text):
        '''
        Apply rules for en dash (pomlcka).

        >>> parser = TxtParser()

        Between numbers:
        >>> parser.parse_en_dash('1996-2010')
        u'1996\u20132010'
        >>> parser.parse_en_dash('2001 - 2002')
        u'2001 \u2013 2002'

        Between specific words (by --):
        >>> parser.parse_en_dash('rychlik Praha--Brno')
        u'rychlik Praha\u2013Brno'
        >>> parser.parse_en_dash('1.--3. misto')
        u'1.\u20133. misto'
        >>> parser.parse_en_dash('Mladost -- radost')
        u'Mladost \u2013 radost'

        As currency mark (,-):
        >>> parser.parse_en_dash('Kcs 30,-')
        u'Kcs 30,\u2013'

        '''

        nums = re.compile(ur'''
                    (?<=[\d ])      # numbers or space before
                    -
                    (?=[\d ]|$)     # numbers or space after
               ''', re.X | re.U)
        substituted = self.sub(nums, u'\u2013', text)

        alphanum = re.compile(ur'''
                        (?<=[^!*+,/:;<=>@\\\\_|-])  # cannot be before
                        --
                        (?=[^!*+,/:;<=>@\\\\_|-])   # cannot be after
                   ''', re.X | re.U)
        substituted = self.sub(alphanum, u'\u2013', substituted)

        curr = re.compile(ur',-')
        substituted = self.sub(curr, ur',\u2013', substituted)

        return substituted

    def parse_dates(self, text):
        '''
        Inserts non breaking space to dates.

        >>> parser = TxtParser()
        >>> parser.parse_dates('Who was born on 28. 3. 1592?')
        u'Who was born on 28.\\xa03.\\xa01592?'
        >>> parser.parse_dates('9. 5.')
        u'9.\\xa05.'

        '''

        with_year = re.compile(ur'(?<!\d)(\d{1,2}\.) (\d{1,2}\.) (\d\d)')
        substituted = with_year.sub(ur'\1\u00a0\2\u00a0\3', text)

        without_year = re.compile(ur'(?<!\d)(\d{1,2}\.) (\d{1,2}\.)')
        substituted = without_year.sub(ur'\1\u00a0\2', substituted)

        return substituted

    def parse_em_dash(self, text):
        '''
        Apply rules and substitutes for em dash.
        Really rare.

        >>> parser = TxtParser()
        >>> parser.parse_em_dash('No --- or yes?')
        u'No\\xa0\u2014 or yes?'

        '''

        pattern = re.compile(ur' --- ')
        return self.sub(pattern, u'\u00a0\u2014 ', text)

    def parse_arrows(self, text):
        '''
        Transform arrows into UTF8 chars.

        >>> parser = TxtParser()
        >>> parser.parse_arrows('In <--> both ways.')
        u'In \u2194 both ways.'
        >>> parser.parse_arrows('To --> the right.')
        u'To \u2192 the right.'
        >>> parser.parse_arrows('And to <-- the left.')
        u'And to \u2190 the left.'
        >>> parser.parse_arrows('Double ==> right.')
        u'Double \u21d2 right.'

        '''

        leftright = re.compile(ur'<-{1,2}>')
        substituted = self.sub(leftright, u'\u2194', text)

        right = re.compile(ur'-{1,}>')
        substituted = self.sub(right, u'\u2192', substituted)

        left = re.compile(ur'<-{1,}')
        substituted = self.sub(left, u'\u2190', substituted)

        double = re.compile(ur'={1,}>')
        substituted = self.sub(double, u'\u21d2', substituted)

        return substituted

    def parse_plusminus(self, text):
        '''
        Transform plusminus to UTF8 char.

        >>> parser = TxtParser()
        >>> parser.parse_plusminus('a = +-10')
        u'a = \\xb110'

        '''

        plusminus = re.compile('\+-')
        return self.sub(plusminus, u'\u00b1', text)

    def parse_dimension(self, text):
        '''
        Transform x to UTF8 char

        >>> parser = TxtParser()
        >>> parser.parse_dimension('10x20')
        u'10\\xd720'
        >>> parser.parse_dimension('120 x 50 cm')
        u'120 \\xd7 50 cm'
        >>> parser.parse_dimension('5x rychleji')
        u'5\\xd7 rychleji'

        '''

        between = re.compile(ur'(\d+)( ?)x\2(?=\d)')
        substituted = self.sub(between, ur'\1\2\u00d7\2', text)

        after = re.compile(ur'(?<=\d)x(?=[ ,.]|$)', re.M)
        substituted = self.sub(after, ur'\u00d7', substituted)

        return substituted

    def parse_quotes(self, text):
        '''
        Transform quotes.

        >>> parser = TxtParser()
        >>> parser.parse_quotes('"Pojd uz," rekla')
        u'\u201ePojd uz,\u201c rekla'
        >>> parser.parse_quotes("'Nepujdu,' odvetil.")
        u'\u201aNepujdu,\u2018 odvetil.'
        >>> parser.parse_quotes("Pad' a chcip'.")
        "Pad' a chcip'."

        '''

        double = re.compile('''
                    (?<!"|\w)           # no " or alphachars before
                    "
                    (?!\ |")            # no space or " after
                    ([^"]+)                # whatever in the middle
                    (?<!\ |")           # no space or " before
                    "
                    (?!")               # no " after
                ''', re.U | re.X | re.M | re.S)
        text = self.sub(double, ur'\u201E\1\u201C', text)

        single = re.compile('''
                    (?<!'|\w)           # no ' or alphachars before
                    '
                    (?!\ |')            # no space or ' after
                    (.+?)               # whatever
                    (?<!\ |')           # no space or ' before
                    '
                    (?!')               # no ' after
                ''', re.U | re.X | re.M | re.S)
        text = self.sub(single, ur'\u201A\1\u2018', text)

        return text

    def parse_prepositions(self, text):
        '''
        Insert non breakable space after some prepositions.

        >>> parser = TxtParser()
        >>> parser.parse_prepositions('Stal opren o zed.')
        u'Stal opren o\\xa0zed.'
        >>> parser.parse_prepositions('Pavouk byl i v jogurtu')
        u'Pavouk byl i\\xa0v\\xa0jogurtu'

        '''

        pattern = re.compile(ur'(?<= |\u00a0)([KkOoSsUuVvZzIiA]) ', re.M)

        return self.sub(pattern, ur'\1\u00a0', text)

    def parse_last_short_words(self, text):
        '''
        Insert non breakable space before short last words.
        '''

        pattern = re.compile(ur'''
                        (?<=.{50})
                        \s+
                        (?=[\x17-\x1F]*\S{1,6}[\x17-\x1F]*$)
                    ''', re.S | re.U | re.X)

        return self.sub(pattern, '\u00a0', text)


class HtmlParser(TxtParser):
    def parse(self):
        '''
        Extract HTML tags, transform text and return back
        HTML into modified text.

        >>> parser = HtmlParser('<hr>')
        >>> parser.parse()
        u'<hr>'

        >>> parser = HtmlParser('<p>Dots...</p>')
        >>> parser.parse()
        u'<p>Dots\u2026</p>'

        >>> parser = HtmlParser('T... --- <-- --> <--> ==> 1x2 +-<i>1</i>')
        >>> parser.parse()
        u'T\u2026\\xa0\u2014 \u2190 \u2192 \u2194 \u21d2 1\\xd72 \\xb1<i>1</i>'

        '''

        html = re.compile('''
                </?\w+((\s+\w+(\s*=\s*(?:".*?"|'.*?'|[^'">\s]+))?)+\s*|\s*)/?>
                ''', re.X)

        self.text = self.sub(html, '', self.text, extract=True)

        text = super(HtmlParser, self).parse()

        self.positions[0] = 0   # fallback
        sorted_positions = sorted(self.positions)

        diff = 0
        for pos in sorted_positions:
            diff += self.positions[pos]
            self.positions[pos] = diff

        for i in sorted(self.extracted, reverse=True):
            for pos in reversed(sorted_positions):
                if pos <= i:
                    diff = self.positions[pos]
                    break

            text = text[:i + diff] + self.extracted[i] + text[i + diff:]

        return text


if __name__ == '__main__':
    import doctest
    doctest.testmod()
