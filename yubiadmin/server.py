from webob.dec import wsgify
from yubiadmin.util.app import render
from yubiadmin.apps import apps


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


class YubiAdmin(object):
    def __init__(self):
        self.apps = {}
        for app in apps:
            app_data = inspect_app(app)
            self.apps[app_data['name']] = (app, app_data)
        self.modules = [data for (_, data) in self.apps.values()]

    @wsgify
    def __call__(self, request):
        module_name = request.path_info_pop()
        section_name = request.path_info_pop()

        if not module_name:
            return render('index', modules=self.modules)

        app, module = self.apps[module_name]
        if not section_name:
            section_name = module['sections'][0]['name']

        section = next(section for section in module['sections']
                       if section['name'] == section_name)

        return render(
            'app_base',
            modules=self.modules,
            module=module,
            section=section,
            title='YubiAdmin - %s - %s' % (module_name, section_name),
            page=app.__getattribute__(section_name)(request)
        )

application = YubiAdmin()
