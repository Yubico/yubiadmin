import cherrypy
import os

from yubiadmin.apps import apps
from jinja2 import Environment, FileSystemLoader


def inspect_app(app):
    cls = app.__class__
    name = cls.name
    doc = app.__doc__.strip()
    title, desc = doc.split('\n', 1)
    desc = desc.strip()
    sections = [{
        'name': section,
        'title': app.__getattribute__(section).__doc__.strip()
    } for section in cls.sections]

    return {
        'name': name,
        'title': title,
        'description': desc,
        'sections': sections,
    }


def render_section(app, section, template, **kwargs):
    data = app.__getattribute__(section)(**kwargs)
    return template.render(**data)


class YubiAdmin(object):
    def __init__(self, env):
        self.env = env
        self.apps = {}
        for app in apps:
            app_data = inspect_app(app)
            self.apps[app_data['name']] = (app, app_data)
        self.modules = [data for (_, data) in self.apps.values()]

    @cherrypy.expose
    def default(self, module_name=None, section_name=None, **kwargs):
        if not module_name:
            tmpl = self.env.get_template('index.html')
            return tmpl.render(modules=self.modules)

        app, module = self.apps[module_name]
        if not section_name:
            section_name = module['sections'][0]['name']

        tmpl = self.env.get_template('%s/%s.html' %
                                     (module_name, section_name))
        section = next(section for section in module['sections']
                       if section['name'] == section_name)

        data = app.__getattribute__(section_name)(**kwargs)
        page = tmpl.render(**data)

        data.update({
            'modules': self.modules,
            'module': module,
            'section': section,
            'title': '%s - %s' % (module_name, section_name),
            'page': page
        })
        tmpl = env.get_template('app_base.html')
        return tmpl.render(**data)

if __name__ == '__main__':
    cwd = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(cwd, os.pardir))
    static_dir = os.path.join(base_dir, 'static')
    template_dir = os.path.join(base_dir, 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))

    conf = {
        '/': {
            'tools.staticdir.root': static_dir,
        }, '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'js',
        }, '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'css',
        }, '/img': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'img',
        }, '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(static_dir,
           'favicon.ico'),
        }
    }

    cherrypy.quickstart(YubiAdmin(env), '/', config=conf)
