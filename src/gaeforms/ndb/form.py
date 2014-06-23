# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from google.appengine.ext.ndb.model import IntegerProperty, StringProperty,DateTimeProperty,DateProperty
from gaeforms.base import IntegerField, Form, _FormMetaclass, DecimalField, StringField, DateField
from ndbext.property import IntegerBounded, SimpleDecimal, SimpleCurrency

_property_to_field_dct = {}


def registry(property_cls, field_cls):
    _property_to_field_dct[property_cls] = field_cls


registry(IntegerProperty, IntegerField)
registry(IntegerBounded, IntegerField)
registry(SimpleDecimal, DecimalField)
registry(SimpleCurrency, DecimalField)
registry(StringProperty, StringField)
registry(DateTimeProperty, DateField)
registry(DateProperty, DateField)


class NotRegisteredProperty(Exception):
    pass


class InvalidParams(Exception):
    pass


def extract_names(properties):
    if properties:
        return set(p._code_name for p in properties)


def make_include_function(include, exclude):
    if include and exclude:
        raise InvalidParams('_include and _exclude can not be not None at same time')

    def should_include(key):
        return True

    if include is not None:
        def should_include(key):
            return key in include
    elif exclude is not None:
        def should_include(key):
            return key not in exclude

    return should_include


class _ModelFormMetaclass(_FormMetaclass):
    def __new__(cls, class_to_be_created_name, bases, attrs):
        model_class = attrs.get('_model_class')
        if model_class:
            properties = model_class._properties
            include = extract_names(attrs.get('_include'))
            exclude = extract_names(attrs.get('_exclude'))

            should_include = make_include_function(include, exclude)

            for k, v in properties.iteritems():
                if should_include(k) and k not in attrs:
                    field_class = _property_to_field_dct.get(v.__class__, None)

                    if field_class is None:
                        msg = 'The %s attribute from class %s has a property not registered: %s' % \
                              (k, class_to_be_created_name, v.__class__)
                        raise NotRegisteredProperty(msg)
                    field = field_class()
                    field.set_options(v)
                    attrs[k] = field
        return super(_ModelFormMetaclass, cls).__new__(cls, class_to_be_created_name, bases, attrs)


class ModelForm(Form):
    __metaclass__ = _ModelFormMetaclass
    _model_class = None
    _include = None
    _exclude = None

    def populate(self, model=None):
        transformed_dct = self.normalize()
        if model:
            model.populate(**transformed_dct)
            return model
        return self._model_class(**transformed_dct)

