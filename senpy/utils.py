from . import models


def check_template(indict, template):
    if isinstance(template, dict) and isinstance(indict, dict):
        for k, v in template.items():
            if k not in indict:
                return '{} not in {}'.format(k, indict)
            check_template(indict[k], v)
    elif isinstance(template, list) and isinstance(indict, list):
        if len(indict) != len(template):
            raise models.Error('Different size for {} and {}'.format(indict, template))
        for e in template:
            found = False
            for i in indict:
                try:
                    check_template(i, e)
                    found = True
                except models.Error as ex:
                    continue
            if not found:
                raise models.Error('{} not found in {}'.format(e, indict))
    else:
        if indict != template:
            raise models.Error('{} and {} are different'.format(indict, template))
