# Copyright (c) 2013 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
from jinja2 import Environment, FileSystemLoader
from webob import exc
from webob.dec import wsgify

__all__ = [
    'App',
    'render',
    'populate_forms',
]

cwd = os.path.dirname(__file__)
base_dir = os.path.abspath(os.path.join(cwd, os.pardir))
template_dir = os.path.join(base_dir, 'templates')
env = Environment(loader=FileSystemLoader(template_dir))


class TemplateBinding(object):
    def __init__(self, template, **kwargs):
        self.template = env.get_template('%s.html' % template)
        self.data = kwargs
        for (key, val) in kwargs.items():
            if isinstance(val, TemplateBinding):
                self.data.update(val.data)

    def extend(self, sub_variable, sub_binding):
        self.data.update(sub_binding.data)
        self.data[sub_variable] = sub_binding

    def __str__(self):
        return self.template.render(self.data)

    @wsgify
    def __call__(self, request):
        return str(self)


def render(tmpl, **kwargs):
    return TemplateBinding(tmpl, **kwargs)


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


class App(object):
    name = None
    sections = []
    priority = 50

    def redirect(self, url):
        raise exc.HTTPSeeOther(location=url)

    def render_forms(self, request, forms, template='form',
                     success_msg='Settings updated!', **kwargs):
        alert = None
        if not request.params:
            for form in forms:
                form.load()
        else:
            errors = False
            for form in forms:
                form.process(request.params)
                errors = not form.validate() or errors
            if not errors:
                try:
                    if success_msg:
                        alert = {'type': 'success', 'title': success_msg}
                    for form in forms:
                        form.save()
                except Exception as e:
                    alert = {'type': 'error', 'title': 'Error:',
                             'message': str(e)}
            else:
                alert = {'type': 'error', 'title': 'Invalid data!'}

        return render(template, target=request.path, fieldsets=forms,
                      alert=alert, **kwargs)
