import re

__all__ = ['validate_email', 'validate_url', 'render_to_string', 'Context', 'mark_safe', 'ValidationError', 'redirect']

try:
    from django.http import HttpResponseRedirect as redirect
    from django.template import RequestContext

    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email
    # noinspection PyUnresolvedReferences
    from django.core.validators import URLValidator
    validate_url = URLValidator()

    try:
        from django.template.loader import get_template_from_string
    except ImportError:  # pragma: no cover
        # Django 1.8+
        # noinspection PyUnresolvedReferences
        from django.template import engines

        def get_template_from_string(template_code, origin=None, name=None):
            del origin, name  # the origin and name parameters seems not to be implemented in django 1.8
            return engines['django'].from_string(template_code)

    # template rendering
    from django.template.context import Context
    from django.template.loader import render_to_string
    from django.utils.safestring import mark_safe

    def get_data_from_request(request):
        return request.POST if request.method == 'POST' else request.GET

except ImportError:
    # werkzeug
    class ValidationError(Exception):
        def __init__(self, messages):
            if isinstance(messages, list):
                self.messages = messages
            else:
                self.messages = [messages]

    def validate_email(email):
        if re.match(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}', email):
            return email
        else:
            raise ValidationError('Enter a valid email address.')

    def validate_url(url):
        if re.match(r'.*://.*\..*', url):
            return url
        else:
            raise ValidationError('Enter a valid URL.')

    import jinja2

    def get_template_from_string(s, name, origin):
        del name, origin
        return jinja2.Template(s)

    Context = dict

    mark_safe = jinja2.Markup

    env = jinja2.Environment(loader=jinja2.PackageLoader('tri.form', 'templates_jinja2'))

    def render_to_string(template_name, context_instance):
        return env.get_template(template_name).render(context_instance)

    from flask import redirect

    def RequestContext(request, d):
        del request
        return Context(d)


    def get_data_from_request(request):
        return request.form
