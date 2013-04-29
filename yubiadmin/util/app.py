import os
from jinja2 import Environment, FileSystemLoader

__all__ = [
    'App',
    'render',
    'populate_forms',
]

cwd = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(cwd, os.pardir))
template_dir = os.path.join(base_dir, 'templates')
env = Environment(loader=FileSystemLoader(template_dir))


def render(tmpl, **kwargs):
    template = env.get_template('%s.html' % tmpl)
    return template.render(**kwargs)


def populate_forms(forms, data):
    if not data:
        for form in forms:
            form.load()
    else:
        errors = False
        for form in forms:
            form.process(data)
            errors = not form.validate() or errors
        if not errors:
            for form in forms:
                form.save()
        else:
            print 'Errors!'


class App(object):
    name = None
    sections = []

    def render_forms(self, request, forms, template='form'):
        populate_forms(forms, request.params)
        return render(template, target=request.path, fieldsets=forms)
