from django.db.models import Model, IntegerField, BooleanField, FloatField, ForeignKey, OneToOneField

saved_something = None


def get_saved_something():
    global saved_something
    return saved_something


class CreateOrEditObjectTest(Model):
    f_int = IntegerField()
    f_float = FloatField()
    f_bool = BooleanField()

    # noinspection PyMethodOverriding
    def save(self):
        global saved_something
        saved_something = self


class FormFromModelTest(Model):
    f_int = IntegerField()
    f_float = FloatField()
    f_bool = BooleanField()

    f_int_excluded = IntegerField()


class Foo(Model):
    foo = IntegerField(help_text='foo_help_text')

    def __repr__(self):
        return 'Foo pk: %s' % self.pk


class FieldFromModelForeignKeyTest(Model):
    foo_fk = ForeignKey(Foo)


class FieldFromModelOneToOneTest(Model):
    foo_one_to_one = OneToOneField(Foo)


class FooField(IntegerField):
    pass


class RegisterFieldFactoryTest(Model):
    foo = FooField()
