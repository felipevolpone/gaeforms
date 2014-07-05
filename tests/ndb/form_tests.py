# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from decimal import Decimal
import unittest
import datetime

from google.appengine.ext import ndb
import webapp2
from webapp2_extras import i18n

from gaeforms.ndb.form import ModelForm, InvalidParams
from gaeforms.ndb.property import IntegerBounded, SimpleCurrency, SimpleDecimal, FloatBounded, Email
from util import GAETestCase
from gaeforms.base import IntegerField


app = webapp2.WSGIApplication(
    [webapp2.Route('/', None, name='upload_handler')])

request = webapp2.Request({'SERVER_NAME': 'test', 'SERVER_PORT': 80,
                           'wsgi.url_scheme': 'http'})
request.app = app
app.set_globals(app=app, request=request)

i18n.default_config['default_timezone'] = 'America/Sao_Paulo'


class IntegerModelMock(ndb.Model):
    integer = ndb.IntegerProperty()
    integer_required = ndb.IntegerProperty(required=True)
    integer_repeated = ndb.IntegerProperty(repeated=True)
    integer_choices = ndb.IntegerProperty(choices=[1, 2])
    integer_default = ndb.IntegerProperty(default=0)


class IntegerModelForm(ModelForm):
    _model_class = IntegerModelMock


class ModelMock(ndb.Model):
    integer = IntegerBounded(required=True, lower=1, upper=2)
    i = ndb.IntegerProperty(default=1)
    f = ndb.FloatProperty(default=2.1)
    float_bounded = FloatBounded(required=True, lower=1.1, upper=3.4)
    currency = SimpleCurrency()
    decimal = SimpleDecimal(decimal_places=3, lower='0.001')
    str = ndb.StringProperty()
    datetime = ndb.DateTimeProperty()
    date = ndb.DateProperty()
    email = Email()


class ModelFormMock(ModelForm):
    _model_class = ModelMock


class ModelFormOverriding(ModelForm):
    _model_class = ModelMock
    integer = IntegerField(required=True)


class ModelFormTests(GAETestCase):
    def test_overriding(self):
        form = ModelFormOverriding(integer='0', float_bounded='2.2')
        self.assertDictEqual({}, form.validate(),
                               'integer with no bounds should be used once it is overriden on ModelValidatorOverriging')

    def test_validate(self):
        form = ModelFormMock(integer='1', float_bounded='2.0')
        self.assertDictEqual({}, form.validate())
        form = ModelFormMock()
        self.assertSetEqual(set(['integer', 'float_bounded']), set(form.validate().keys()))
        form = ModelFormMock(integer='0', float_bounded=3.41)
        self.assertSetEqual(set(['integer', 'float_bounded']), set(form.validate().keys()))
        form = ModelFormMock(integer='1',
                             decimal='0.001',
                             currency='0.01',
                             float_bounded='2.0',
                             str='a',
                             email='foo@bar.com',
                             datetime='30/09/2000 23:56:56',
                             date='08/01/1999')
        self.assertDictEqual({}, form.validate())
        form = ModelFormMock(integer='0',
                             decimal='0.0001',
                             currency='-0.01',
                             str='a' * 501,
                             email='foo@bar',
                             datetime='a/09/30 23:56:56',
                             date='1999/08/a1')
        self.assertSetEqual(set(['integer',
                                 'decimal',
                                 'currency',
                                 'str',
                                 'email',
                                 'datetime',
                                 'float_bounded',
                                 'date']),
                            set(form.validate().keys()))

    def test_populate_model(self):
        model_form = ModelFormMock(integer='1',
                                   decimal='0.001',
                                   currency='0.01',
                                   float_bounded='2.2',
                                   str='a',
                                   email='foo@bar.com',
                                   datetime='09/30/2000 23:56:56',
                                   date='08/01/1999')
        property_dct = {'integer': 1,
                        'i': 1,
                        'float_bounded': 2.2,
                        'f': 2.1,
                        'email':'foo@bar.com',
                        'decimal': Decimal('0.001'),
                        'currency': Decimal('0.01'),
                        'str': 'a',
                        'datetime': datetime.datetime(2000, 10, 1, 2, 56, 56),
                        'date': datetime.date(1999, 8, 1)}
        model = model_form.populate_model()
        self.assertIsInstance(model, ModelMock)
        self.assertDictEqual(property_dct, model.to_dict())
        model_key = model.put()
        model_form = ModelFormMock(integer='2',
                                   decimal='3.001',
                                   currency='4.01',
                                   float_bounded='2.5',
                                   email='foo@bar.com',
                                   str='b',
                                   datetime='09/30/2000 23:56:56',
                                   date='08/01/1999')
        property_dct = {'integer': 2,
                        'i': 1,
                        'f': 2.1,
                        'email':'foo@bar.com',
                        'float_bounded': 2.5,
                        'decimal': Decimal('3.001'),
                        'currency': Decimal('4.01'),
                        'str': 'b',
                        'datetime': datetime.datetime(2000, 10, 1, 2, 56, 56),
                        'date': datetime.date(1999, 8, 1)}
        model_form.populate_model(model)
        self.assertIsInstance(model, ModelMock)
        self.assertDictEqual(property_dct, model.to_dict())
        self.assertEqual(model_key, model.key)

    def test_populate_form(self):
        model_form = ModelFormMock()
        model = ModelMock(integer=1,
                          decimal=Decimal('0.001'),
                          currency=Decimal('0.01'),
                          float_bounded=2.6,
                          email='foo@bar.com',
                          str='a',
                          datetime=datetime.datetime(2000, 9, 30, 23, 56, 56),
                          date=datetime.datetime(1999, 8, 1))
        localized_dct = model_form.populate_form(model)
        self.assertDictEqual({'integer': '1',
                              'i': '1',
                              'float_bounded': '2.6',
                              'f': '2.1',
                              'email':'foo@bar.com',
                              'decimal': '0.001',
                              'currency': '0.01',
                              'str': 'a',
                              'datetime': '09/30/2000 20:56:56',
                              'date': '08/01/1999'}, localized_dct)

    def test_populate_form_model_with_defaults(self):
        class ModelWithDefaults(ndb.Model):
            integer = IntegerBounded(lower=1, upper=2)
            i = ndb.IntegerProperty()
            f = ndb.FloatProperty()
            float_bounded = FloatBounded(lower=1.1, upper=3.4)
            currency = SimpleCurrency()
            decimal = SimpleDecimal(decimal_places=3, lower='0.001')
            str = ndb.StringProperty()
            dtime = ndb.DateTimeProperty()
            dt = ndb.DateProperty()

        class FormDefaults(ModelForm):
            _model_class = ModelWithDefaults

        form = FormDefaults()
        model = ModelWithDefaults()
        model.put()
        form.populate_form(model)

        self.assertEqual('', form.integer)
        self.assertEqual('', form.dtime)  # different because of timezone
        self.assertEqual('', form.dt)
        self.assertEqual('', form.integer)
        self.assertEqual('', form.i)
        self.assertEqual('', form.f)
        self.assertEqual('', form.float_bounded)
        self.assertEqual('', form.currency)
        self.assertEqual('', form.decimal)


class IntegerModelFormTests(unittest.TestCase):
    def test_fields(self):
        properties = ['integer', 'integer_required', 'integer_repeated',
                      'integer_choices', 'integer_default']
        self.assertSetEqual(set(properties), set(IntegerModelForm._fields.iterkeys()))
        for p in properties:
            self.assertIsInstance(IntegerModelForm._fields[p], IntegerField)

    def test_include(self):
        properties = ['integer', 'integer_required']

        class IntegerInclude(ModelForm):
            _model_class = IntegerModelMock
            _include = (IntegerModelMock.integer, IntegerModelMock.integer_required)

        self.assertSetEqual(set(properties), set(IntegerInclude._fields.iterkeys()))
        for p in properties:
            self.assertIsInstance(IntegerInclude._fields[p], IntegerField)

    def test_exclude(self):
        properties = ['integer_repeated', 'integer_choices', 'integer_default']

        class IntegerInclude(ModelForm):
            _model_class = IntegerModelMock
            _exclude = (IntegerModelMock.integer, IntegerModelMock.integer_required)

        self.assertSetEqual(set(properties), set(IntegerInclude._fields.iterkeys()))
        for p in properties:
            self.assertIsInstance(IntegerInclude._fields[p], IntegerField)

    def test_include_exclude_definition_error(self):

        def f():
            class IntegerInclude(ModelForm):
                _model_class = IntegerModelMock
                _exclude = (IntegerModelMock.integer, IntegerModelMock.integer_required)
                _include = (IntegerModelMock.integer, IntegerModelMock.integer_required)

        self.assertRaises(InvalidParams, f)

    def test_property_options(self):
        self.assertTrue(IntegerModelForm._fields['integer_required'].required)
        self.assertTrue(IntegerModelForm._fields['integer_repeated'].repeated)
        self.assertSetEqual(frozenset([1, 2]), IntegerModelForm._fields['integer_choices'].choices)
        self.assertEqual(0, IntegerModelForm._fields['integer_default'].default)
