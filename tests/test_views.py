from __future__ import absolute_import

import json

import pytest
from bs4 import BeautifulSoup
from tri_struct import Struct, merged

from tests.test_forms import remove_csrf
from tri_form import INITIALS_FROM_GET, DISPATCH_PATH_SEPARATOR
from tri_form.views import create_object, edit_object, create_or_edit_object_redirect


def get_request_context(response):
    if 'context_instance' in response:
        return response['context_instance']
    return response['context']


@pytest.mark.django_db
def test_create_or_edit_object():
    from tests.models import CreateOrEditObjectTest, get_saved_something, Foo, reset_saved_something

    reset_saved_something()

    # 1. View create form
    request = Struct(method='GET', META={}, GET={}, user=Struct(is_authenticated=lambda: True))

    response = create_object(
        request=request,
        model=CreateOrEditObjectTest,
        render__call_target=lambda **kwargs: kwargs,
        model_verbose_name='baz',
    )
    assert get_request_context(response)['object_name'] == 'baz'  # check explicit model_verbose_name parameter to create_object
    assert get_request_context(response)['csrf_token']

    response = create_object(
        request=request,
        model=CreateOrEditObjectTest,
        form__field__f_int__initial=1,
        form__field__f_float__initial=lambda form, field: 2,
        template_name='<template name>',
        render=lambda **kwargs: kwargs,  # this is the same as render__call_target=...
        render__context={'foo': 'FOO'},
        render__foobarbaz='render__foobarbaz',
    )
    assert get_request_context(response)['object_name'] == 'foo bar'  # Meta verbose_name
    assert get_request_context(response)['is_create'] is True
    form = get_request_context(response)['form']
    assert get_request_context(response)['foo'] == 'FOO'
    assert get_request_context(response)['csrf_token']
    assert response['foobarbaz'] == 'render__foobarbaz'
    assert response['template_name'] == '<template name>'
    assert form.mode is INITIALS_FROM_GET
    assert form.fields_by_name['f_int'].initial == 1
    assert form.fields_by_name['f_int'].errors == set()
    assert form.fields_by_name['f_int'].value == 1
    assert form.fields_by_name['f_float'].value == 2
    assert form.fields_by_name['f_bool'].value is None
    assert set(form.fields_by_name.keys()) == {'f_int', 'f_float', 'f_bool', 'f_foreign_key', 'f_many_to_many'}

    # 2. Create
    foo = Foo.objects.create(foo=7)

    request.method = 'POST'
    request.POST = {
        'f_int': '3',
        'f_float': '5.1',
        'f_bool': 'True',
        'f_foreign_key': str(foo.pk),
        'f_many_to_many': [str(foo.pk)],
        f'{DISPATCH_PATH_SEPARATOR}': '',
    }

    def on_save(form, instance, **_):
        # validate  that the arguments are what we expect
        assert form.instance is instance
        assert isinstance(instance, CreateOrEditObjectTest)
        assert instance.pk is not None

    response = create_object(
        request=request,
        model=CreateOrEditObjectTest,
        on_save=on_save,  # just to check that we get called with the instance as argument
        render=lambda **kwargs: kwargs,
    )
    instance = get_saved_something()
    reset_saved_something()
    assert instance is not None
    assert instance.f_int == 3
    assert instance.f_float == 5.1
    assert instance.f_bool is True
    assert response.status_code == 302
    assert response['Location'] == '../'

    # 3. View edit form
    request.method = 'GET'
    del request.POST
    response = edit_object(
        request=request,
        instance=instance,
        render__call_target=lambda **kwargs: kwargs)
    form = get_request_context(response)['form']
    assert form.get_errors() == {}
    assert form.fields_by_name['f_int'].value == 3
    assert form.fields_by_name['f_float'].value == 5.1
    assert form.fields_by_name['f_bool'].value is True
    assert get_request_context(response)['csrf_token']

    # 4. Edit
    request.method = 'POST'
    request.POST = {
        'f_int': '7',
        'f_float': '11.2',
        'f_foreign_key': str(foo.pk),
        'f_many_to_many': [str(foo.pk)],
        f'{DISPATCH_PATH_SEPARATOR}': '',
        # Not sending a parameter in a POST is the same thing as false
    }
    response = edit_object(
        request=request,
        instance=instance,
        redirect=lambda form, **_: {'context_instance': {'form': form}},
        render__call_target=lambda **kwargs: kwargs,
    )
    instance = get_saved_something()
    reset_saved_something()
    form = get_request_context(response)['form']
    assert form.get_errors() == {}
    assert form.is_valid() is True
    assert instance is not None
    assert instance.f_int == 7
    assert instance.f_float == 11.2
    assert not instance.f_bool

    # edit again, to check redirect
    response = edit_object(
        request=request,
        instance=instance,
    )
    assert response.status_code == 302
    assert response['Location'] == '../../'


def test_redirect_default_case():
    sentinel1, sentinel2, sentinel3, sentinel4 = object(), object(), object(), object()
    expected = dict(redirect_to=sentinel2, request=sentinel3, form=sentinel4)
    assert create_or_edit_object_redirect(**merged(expected, is_create=sentinel1, redirect=lambda **kwargs: kwargs)) == expected


@pytest.mark.django_db
def test_unique_constraint_violation():
    from tests.models import UniqueConstraintTest

    request = Struct(method='POST', META={}, GET={}, user=Struct(is_authenticated=lambda: True))
    request.POST = {
        'f_int': '3',
        'f_float': '5.1',
        'f_bool': 'True',
        f'{DISPATCH_PATH_SEPARATOR}': '',
    }
    create_object(
        request=request,
        model=UniqueConstraintTest)
    assert UniqueConstraintTest.objects.all().count() == 1

    response = create_object(
        request=request,
        model=UniqueConstraintTest,
        render__call_target=lambda **kwargs: kwargs)

    form = get_request_context(response)['form']
    assert form.is_valid() is False
    assert form.get_errors() == {'global': {'Unique constraint test with this F int, F float and F bool already exists.'}}
    assert UniqueConstraintTest.objects.all().count() == 1


@pytest.mark.django_db
def test_namespace_forms():
    from tests.models import get_saved_something, reset_saved_something, NamespaceFormsTest

    reset_saved_something()

    # Create object
    request = Struct(method='POST', META={}, GET={}, user=Struct(is_authenticated=lambda: True))
    request.POST = {
        'f_int': '3',
        'f_float': '5.1',
        'f_bool': 'True',
        f'{DISPATCH_PATH_SEPARATOR}': '',
    }
    response = create_object(
        request=request,
        model=NamespaceFormsTest,
        on_save=lambda instance, **_: instance,  # just to check that we get called with the instance as argument
        render__call_target=lambda **kwargs: kwargs)
    instance = get_saved_something()
    reset_saved_something()
    assert instance is not None
    assert response.status_code == 302

    form_name = 'create_or_edit_object_form'
    # Edit should NOT work when the form name does not match the POST
    request.POST = {
        form_name + DISPATCH_PATH_SEPARATOR + 'f_int': '7',
        form_name + DISPATCH_PATH_SEPARATOR + 'f_float': '11.2',
        DISPATCH_PATH_SEPARATOR + 'some_other_form': '',
    }
    response = edit_object(
        request=request,
        instance=instance,
        form__name=form_name,
        render__call_target=lambda **kwargs: kwargs)
    form = get_request_context(response)['form']
    assert form.get_errors() == {}
    assert form.is_valid() is True
    assert not form.is_target()
    assert instance is not None
    assert instance.f_int == 3
    assert instance.f_float == 5.1
    assert instance.f_bool

    # Edit should work when the form name is in the POST
    del request.POST[DISPATCH_PATH_SEPARATOR + 'some_other_form']
    request.POST[DISPATCH_PATH_SEPARATOR + form_name] = ''
    response = edit_object(
        request=request,
        instance=instance,
        redirect=lambda form, **_: {'context_instance': {'form': form}},
        form__name=form_name,
        render__call_target=lambda **kwargs: kwargs)
    form = get_request_context(response)['form']
    instance = get_saved_something()
    reset_saved_something()
    assert form.get_errors() == {}
    assert form.is_valid() is True
    assert form.is_target()
    assert instance is not None
    assert instance.f_int == 7
    assert instance.f_float == 11.2
    assert not instance.f_bool


@pytest.mark.django_db
@pytest.mark.filterwarnings("ignore:Pagination may yield inconsistent results with an unordered")
def test_create_or_edit_object_dispatch():
    from tests.models import Bar, Foo

    f1 = Foo.objects.create(foo=1)
    f2 = Foo.objects.create(foo=2)
    request = Struct(method='GET', META={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}, GET={DISPATCH_PATH_SEPARATOR + 'field' + DISPATCH_PATH_SEPARATOR + 'foo': ''}, user=Struct(is_authenticated=lambda: True))

    response = create_object(
        request=request,
        model=Bar,
        form__field__foo__extra__endpoint_attr='foo',
        template_name='<template name>',
        render=lambda **kwargs: kwargs,
        render__context={'foo': 'FOO'},
    )
    assert json.loads(response.content) == dict(
        results=[
            {"text": str(f1), "id": f1.pk},
            {"text": str(f2), "id": f2.pk},
        ],
        more=False,
        page=1,
    )


@pytest.mark.django_db
def test_create_object_default_template():
    from tests.models import Foo

    request = Struct(method='GET', META={}, GET={}, user=Struct(is_authenticated=lambda: True))

    response = create_object(request=request, model=Foo)
    assert response.status_code == 200

    expected_html = """
        <div class="form_buttons clear">
            <div class="links">
                <input accesskey="s" class="button" type="submit" value="Create foo"/>
            </div>
        </div>
    """
    actual = BeautifulSoup(response.content, 'html.parser').select('.form_buttons')[0].prettify()
    expected = BeautifulSoup(expected_html, 'html.parser').prettify()
    assert actual == expected


@pytest.mark.django_db
def test_edit_object_default_template():
    from tests.models import Foo

    request = Struct(method='GET', META={}, GET={}, user=Struct(is_authenticated=lambda: True))

    response = edit_object(request=request, instance=Foo.objects.create(foo=1))
    assert response.status_code == 200

    expected_html = """
        <div class="form_buttons clear">
            <div class="links">
                <input accesskey="s" class="button" type="submit" value="Save foo"/>
            </div>
        </div>
    """
    actual = BeautifulSoup(response.content, 'html.parser').select('.form_buttons')[0].prettify()
    expected = BeautifulSoup(expected_html, 'html.parser').prettify()
    assert actual == expected


@pytest.mark.django_db
def test_create_or_edit_object_default_template_with_name():
    from tests.models import Foo

    request = Struct(method='GET', META={}, GET={}, user=Struct(is_authenticated=lambda: True))

    response = create_object(request=request, model=Foo, form__name='form_name', form__endpoint_dispatch_prefix='form_name')
    assert response.status_code == 200

    expected_html = """
        <div class="form_buttons clear">
            <div class="links">
                <input accesskey="s" class="button" name="/form_name" type="submit" value="Create foo"/>
            </div>
        </div>
    """
    actual = BeautifulSoup(response.content, 'html.parser').select('.form_buttons')[0].prettify()
    expected = BeautifulSoup(expected_html, 'html.parser').prettify()
    assert actual == expected


@pytest.mark.django_db
def test_create_or_edit_object_validate_unique():
    from tests.models import Baz

    request = Struct(
        method='POST',
        META={},
        GET={},
        POST={
            'a': '1',
            'b': '1',
            f'{DISPATCH_PATH_SEPARATOR}': '',
        },
        user=Struct(is_authenticated=lambda: True),
    )

    response = create_object(request=request, model=Baz)
    assert response.status_code == 302
    assert Baz.objects.filter(a=1, b=1).exists()

    response = create_object(request=request, model=Baz)
    assert response.status_code == 200
    assert 'Baz with this A and B already exists.' in response.content.decode('utf-8')

    request.POST['b'] = '2'
    response = create_object(request=request, model=Baz)
    assert response.status_code == 302
    instance = Baz.objects.get(a=1, b=2)

    request.POST['b'] = '1'
    response = edit_object(request=request, instance=instance)
    assert response.status_code == 200
    assert 'Baz with this A and B already exists.' in response.content.decode('utf-8')


@pytest.mark.django_db
@pytest.mark.parametrize('name', [None, 'baz'])
def test_create_or_edit_object_full_template(name):
    from tests.models import Foo

    request = Struct(method='GET', META={}, GET={}, user=Struct(is_authenticated=lambda: True))

    response = create_object(request=request, model=Foo, form__name=name, form__endpoint_dispatch_prefix=name)
    assert response.status_code == 200

    prefix = '' if not name else name + '/'
    name_attr = '' if not name else f'name="/{name}" '

    expected_html = f"""
<html>
    <head>Create foo</head>
    <body>
        <form action="" method="post"><input type="hidden" name="csrfmiddlewaretoken" value="vt93bLZuhPhOAMvMFcyIOOXHYU3PCY0csFyUusDbb22FErp1uefHKD4JbMaa1SFr"/>
            <div class="tablewrapper">
                <table class="formview" width="100%">
                    <tr class="required">
                        <td class="description_container">
                            <div class="formlabel"><label for="id_foo">Foo</label></div>
                            <div class="formdescr">foo_help_text</div>
                        </td>
                        <td>
                            <input type="text" value="" name="{prefix}foo" id="id_foo">
                        </td>
                    </tr>
                    <input type="hidden" name="-{name or ''}" value=""/>
                </table>
            </div>
            <div class="form_buttons clear">
                <div class="links">
                    &nbsp;
                    <input accesskey="s" class="button" {name_attr}type="submit" value="Create foo"></input>
                </div>
            </div>
        </form>
    </body>
</html>
    """
    actual = remove_csrf(BeautifulSoup(response.content, 'html.parser').prettify())
    expected = remove_csrf(BeautifulSoup(expected_html, 'html.parser').prettify())
    assert actual == expected
