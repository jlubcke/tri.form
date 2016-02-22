from __future__ import unicode_literals, absolute_import
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.template.loader import render_to_string
from tri.declarative import extract_subkeys

from tri.form import Form


def edit_object(
        request,
        instance,
        redirect_to=None,
        on_save=lambda **kwargs: None,
        render=render_to_string,
        redirect=lambda request, redirect_to: HttpResponseRedirect(redirect_to),
        **kwargs):
    assert 'is_create' not in kwargs
    assert 'model' not in kwargs
    model = instance.__class__
    return create_or_edit_object(
        request,
        model,
        is_create=False,
        instance=instance,
        redirect_to=redirect_to,
        on_save=on_save,
        render=render,
        redirect=redirect,
        **kwargs)


def create_object(
        request,
        model,
        redirect_to=None,
        on_save=lambda **kwargs: None,
        render=render_to_string,
        redirect=lambda request, redirect_to: HttpResponseRedirect(redirect_to),
        **kwargs):
    assert 'is_create' not in kwargs
    return create_or_edit_object(
        request,
        model,
        is_create=True,
        redirect_to=redirect_to,
        on_save=on_save,
        render=render,
        redirect=redirect,
        **kwargs)


def create_or_edit_object(
        request,
        model,
        is_create,
        instance=None,
        redirect_to=None,
        on_save=lambda **kwargs: None,
        render=render_to_string,
        redirect=lambda request, redirect_to: HttpResponseRedirect(redirect_to),
        **kwargs):
    kwargs.setdefault('form__class', Form.from_model)
    kwargs.setdefault('template_name', 'tri_form/create_or_edit_object_block.html')
    p = extract_subkeys(kwargs, 'form', defaults={'model': model, 'instance': instance, 'data': request.POST if request.method == 'POST' else None})
    form = kwargs['form__class'](**p)

    # noinspection PyProtectedMember
    model_verbose_name = kwargs.get('model_verbose_name', model._meta.verbose_name.replace('_', ' '))

    if request.method == 'POST' and form.is_valid():
        if is_create:
            assert instance is None
            instance = model()
        form.apply(instance)
        instance.save()

        kwargs['instance'] = instance
        on_save(**kwargs)

        return create_or_edit_object_redirect(is_create, redirect_to, request, redirect)

    c = {
        'form': form,
        'is_create': is_create,
        'object_name': model_verbose_name,
    }
    c.update(kwargs.get('render__context', {}))

    kwargs_for_render = extract_subkeys(kwargs, 'render', {
        'context_instance': RequestContext(request, c),
        'template_name': kwargs['template_name'],
    })
    return render(**kwargs_for_render)


def create_or_edit_object_redirect(is_create, redirect_to, request, redirect):
    if redirect_to is None:
        if is_create:
            redirect_to = "../"
        else:
            redirect_to = "../../"  # We guess here that the path ends with '<pk>/edit/' so this should end up at a good place
    return redirect(request, redirect_to)
