# coding=utf8

TRANSLATIONS = {
    u'pt-br': {
        u'Worked': u'Trabalhado',
        u'Balance': u'Saldo',
        u'day': u'dia',
        u'type': u'tipo',
        u'in': u'entrada',
        u'out': u'saída',
        u'worked': u'trabalhado',
        u'balance': u'saldo',
        u'NOR': u'NORMAL',
        u'WE': u'FDS',
        u'HOL': u'FERIADO',
        u'VAC': u'FERIAS',
        u'ABS': u'FALTA',
        u'COM': u'COMPENSACAO',
        u'Z': u'OUTRO',
    },
    u'en-us': {},
}


def get_translations(lang):
    if not lang:
        return None

    lang = lang.lower().replace('_', '-')
    translations = TRANSLATIONS.get(lang)
    if translations is None:
        raise ValueError('Language not available: {}'.format(lang))
    return translations
