from sqlalchemy import Column, Integer, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base, declared_attr


Base = declarative_base()


class Model(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__ + 'Table'

    pk = Column(Integer, primary_key=True)


class CreateOrEditObjectTest(Model, Base):
    f_int = Column(Integer)
    f_float = Column(Float)
    f_bool = Column(Boolean)


class FormFromModelTest(Model, Base):
    f_int = Column(Integer)
    f_float = Column(Float)
    f_bool = Column(Boolean)

    f_int_excluded = Column(Integer)


class Foo(Model, Base):
    foo = Column(Integer)

    def __repr__(self):
        return 'Foo pk: %s' % self.pk


# class FieldFromModelForeignKeyTest(Model, Base):
#     foo_fk = Column(Integer, ForeignKey('Foo.pk'))


# class FieldFromModelOneToOneTest(Model, Base):
#     child_id = Column(Integer, ForeignKey('foo.id'))
#     child = relationship("Foo", backref=backref("parent", uselist=False))


# class FooField(IntegerField):
#     pass
#
#
# class RegisterFieldFactoryTest(Model):
#     foo = FooField()
