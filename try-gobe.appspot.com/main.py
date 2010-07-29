from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import users
from google.appengine.ext.webapp import template
from django.utils import simplejson
import hashlib
import datetime

import os.path as op
from models import Annotation

template_dir = op.join(op.dirname(__file__), "templates")
def render(path, vals=None, **kwargs):
    if vals is None: vals = {}
    vals.update(kwargs)
    path = op.join(template_dir, path)
    return template.render(path, vals)

def user_stuff(uri):
    if users.get_current_user():
        url = users.create_logout_url(uri)
        url_text = 'Logout'
    else:
        url = users.create_login_url(uri)
        url_text = 'Login'
    return {'login_url': url, 'login_url_text': url_text}


class Index(webapp.RequestHandler):
    def get(self, anno_id=''):
        user = users.get_current_user()
        if anno_id == "":
            a = Annotation.all().order("-date").get()
        else:
            a = Annotation.all().filter('id = ', anno_id).get()
        if a is None: a = Annotation()
        user_tmpl = user_stuff(self.request.uri)
        history = Annotation.all().order("-date").fetch(20)
        name = user and user.nickname() or "anonymous"
        self.response.out.write(render("index.html", user_tmpl, anno_name=name, anno_id=a.anno_id or "",
                                       anno_content=a.content or "", anno_title=a.title or "",
                                       history=history))

    def post(self, unused):
        self.response.headers['Content-type'] = 'text/javascript';
        user = users.get_current_user()
        annos = self.request.get('annos', '').strip()
        if not annos:
            simplejson.dumps({'status': 'fail'})
            return
        name = user and user.nickname() or "anonymous"
        title = self.request.get('title', name + "|" + str(datetime.datetime.now()))
        id = hashlib.md5(annos + title).hexdigest()
        a = Annotation(title=title, author=user, content=annos.strip(), anno_id=id)
        a.put()
        self.response.out.write(simplejson.dumps({'status':'success', 'id': id}))

class Anno(webapp.RequestHandler):
    def get(self, anno_id):
        self.response.headers['Content-type'] = 'text/plain';
        if anno_id == "":
            a = Annotation.all().order("-date").get()
        elif anno_id == "all":
            pass
        else:
            a = Annotation.all().filter('anno_id = ', anno_id).get()
        if a is None: a = Annotation()

        self.response.out.write(a.content or "")

urls = (
    ('/annos/(.*)', Anno),
    ('/(.*)', Index),
)
application = webapp.WSGIApplication(urls, debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
