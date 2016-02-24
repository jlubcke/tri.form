from __future__ import absolute_import

from tests_flask.models import CreateOrEditObjectTest, Base
from tri.struct import Struct

from tri.form.views import create_object, edit_object


def test_create_or_edit_object():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine('sqlite:///:memory:', echo=True)
    Session = sessionmaker(bind=engine)
    Session.configure(bind=engine)
    session = Session()
    db = Struct(session=session)
    Base.metadata.create_all(engine)

    # 1. View create form
    request = Struct(method='GET', META={}, user=Struct(is_authenticated=lambda: True))

    response = create_object(
        request=request,
        model=CreateOrEditObjectTest,
        form__f_int__initial=1,
        form__f_float__initial=lambda form, field: 2,
        save__db=db,
        render=lambda **kwargs: kwargs)
    assert response['context_instance']['object_name'] == 'create or edit object test'
    assert response['context_instance']['is_create'] == True
    form = response['context_instance']['form']
    assert not form.should_parse
    assert form.fields_by_name['f_int'].initial == 1
    assert form.fields_by_name['f_int'].errors == set()
    assert form.fields_by_name['f_int'].value == 1
    assert form.fields_by_name['f_float'].value == 2
    assert form.fields_by_name['f_bool'].value is None

    # 2. Create
    request.method = 'POST'
    request.form = {
        'f_int': '3',
        'f_float': '5.1',
        'f_bool': 'True',
    }
    create_object(
        request=request,
        model=CreateOrEditObjectTest,
        save__db=db,
        render=lambda **kwargs: kwargs)
    s, = session.query(CreateOrEditObjectTest)
    assert s is not None
    assert s.f_int == 3
    assert s.f_float == 5.1
    assert s.f_bool is True

    # 3. View edit form
    request.method = 'GET'
    request.form = {}
    response = edit_object(
        request=request,
        instance=s,
        save__db=db,
        render=lambda **kwargs: kwargs)
    form = response['context_instance']['form']
    assert form.fields_by_name['f_int'].value == 3
    assert form.fields_by_name['f_float'].value == 5.1
    assert form.fields_by_name['f_bool'].value is True

    # 4. Edit
    request.method = 'POST'
    request.form = {
        'f_int': '7',
        'f_float': '11.2',
        # Not sending a parameter in a POST is the same thing as false
    }
    edit_object(
        request=request,
        instance=s,
        save__db=db,
        render=lambda **kwargs: kwargs)
    s, = session.query(CreateOrEditObjectTest)
    assert s is not None
    assert s.f_int == 7
    assert s.f_float == 11.2
    assert not s.f_bool
