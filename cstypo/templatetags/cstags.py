from cstypo import parser

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def typify(text, type='txt'):
    '''
    Apply typography rules to input text.

    Simple text:
    >>> typify('Arrow -->')
    u'Arrow \u2192'
    >>> typify('<img src="byl u stolu.png"> U stolu')
    u'<img src=\u201ebyl u\\xa0stolu.png\u201c> U\\xa0stolu'

    HTML:
    >>> typify('<img src="byl u stolu.png"> U stolu', type='html')
    u'<img src="byl u stolu.png"> U\\xa0stolu'
    '''

    if type == 'txt':
        inst = parser.TxtParser(text)
        safe = mark_safe
    else:
        inst = parser.HtmlParser(text)
        safe = lambda text: text

    return safe(inst.parse())


if __name__ == '__main__':
    import doctest
    doctest.testmod()
