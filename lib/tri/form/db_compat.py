import re

from tri.declarative import collect_namespaces, assert_kwargs_empty


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

try:
    from django.db.models import AutoField
    import django

    def get_fields(model):
        for field, _ in model._meta.get_fields_with_model():
            yield field

    def is_primary_key_field(field):
        return isinstance(field, AutoField)

    def is_nullable(model_field):
        return model_field.null

    def is_blankable(model_field):
        return model_field.blank

    def get_field_verbose_name(model_field):
        return model_field.verbose_name

    def get_model_verbose_name(model):
        return model._meta.verbose_name

    def save_instance(instance):
        instance.save()

    def create_from_model(default_factory, model, include=None, exclude=None, extra=None, **kwargs):
        def should_include(name):
            if exclude is not None and name in exclude:
                return False
            if include is not None:
                return name in include
            return True

        kwargs = collect_namespaces(kwargs)

        fields = []
        # noinspection PyProtectedMember
        for field in get_fields(model):
            if should_include(field.name):
                subkeys = kwargs.pop(field.name, {})
                subkeys.setdefault('class', default_factory)
                if is_primary_key_field(field):
                    subkeys.setdefault('show', False)
                foo = subkeys.pop('class')(name=field.name, model=model, model_field=field, **subkeys)
                if isinstance(foo, list):
                    fields.extend(foo)
                else:
                    fields.append(foo)
        assert_kwargs_empty(kwargs)
        return fields + (extra if extra is not None else [])


except ImportError:
    from sqlalchemy import inspect

    def get_fields(model):
        return inspect(model).columns

    def is_primary_key_field(field):
        return field.primary_key

    def is_nullable(model_field):
        return model_field.nullable

    def is_blankable(model_field):  # pragma: no cover
        del model_field
        return True

    def get_field_verbose_name(model_field):
        return model_field.name

    def get_model_verbose_name(model):
        return camel_to_snake(model.__name__)

    def save_instance(instance, db):
        db.session.add(instance)
        db.session.commit()