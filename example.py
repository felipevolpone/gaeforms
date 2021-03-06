# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from google.appengine.ext.ndb.model import Model, IntegerProperty, StringProperty, BooleanProperty
from gaeforms.country.br.property import CepProperty
from gaeforms.ndb.form import ModelForm
import os
import sys

if 'GAE_SDK' in os.environ:
    SDK_PATH = os.environ['GAE_SDK']

    sys.path.insert(0, SDK_PATH)

    import dev_appserver

    dev_appserver.fix_sys_path()

# workaroung to enable i18n tests
import webapp2

app = webapp2.WSGIApplication(
    [webapp2.Route('/', None, name='upload_handler')])

request = webapp2.Request({'SERVER_NAME': 'test', 'SERVER_PORT': 80,
                           'wsgi.url_scheme': 'http'})
request.app = app
app.set_globals(app=app, request=request)
# end fo workaround

from gaeforms.base import Form, StringField, IntegerField


class User(Model):
    name = StringProperty(required=True)
    age = IntegerProperty()


class UserForm(ModelForm):
    _model_class = User


class Address(Model):
    cep_declared = BooleanProperty(default=False)
    cep = CepProperty()


class AddressForm(ModelForm):
    _model_class = Address

    def validate(self):
        errors = super(AddressForm, self).validate()
        normalized_dct = self.normalize()
        if normalized_dct['cep_declared'] == True and not self.cep:
            errors['cep'] = 'If CEP is declared it should not be empty'
        return errors
