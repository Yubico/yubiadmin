import os
import re
from UserDict import DictMixin
from wtforms import Form
from jinja2 import Environment, FileSystemLoader

__all__ = [
    'App',
    'FileConfig',
    'ConfigForm',
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

    def render_forms(self, request, forms):
        populate_forms(forms, request.params)
        return render('form', target=request.path, fieldsets=forms)


class ValueHandler(object):
    def __init__(self, pattern, writer, default=None, group=1):
        self.pattern = re.compile(pattern)
        self.writer = writer
        self.default = default
        self.group = group

    def read(self, content):
        match = self.pattern.search(content)
        if match:
            return match.group(self.group)
        return self.default

    def write(self, content, value):
        if value is None:
            value = ''
        if self.pattern.search(content):
            content = self.pattern.sub(self.writer(value), content, 1)
        else:
            content += os.linesep + self.writer(value)
        return content


class FileConfig(DictMixin):
    def __init__(self, filename, params=[]):
        self.filename = filename
        self.params = {}
        for param in params:
            self.add_param(*param)

    def read(self):
        try:
            with open(self.filename, 'r') as file:
                self.content = file.read()
        except IOError as e:
            print e
            self.content = ''

    def commit(self):
        with open(self.filename, 'w+') as file:
            file.write(self.content)

    def add_param(self, key, pattern, writer, default=None, group=1):
        self.params[key] = ValueHandler(pattern, writer, default, group)

    def __getitem__(self, key):
        return self.params[key].read(self.content)

    def __setitem__(self, key, value):
        self.content = self.params[key].write(self.content, value)

    def keys(self):
        return self.params.keys()

    def __delitem__(self, key):
        del self.params[key]


class ConfigForm(Form):
    config = None

    def load(self):
        self.config.read()
        for field in self:
            if field.id in self.config:
                field.process_data(self.config[field.id])

    def save(self):
        self.config.read()
        for field in self:
            if field.id in self.config:
                self.config[field.id] = field.data
        self.config.commit()
