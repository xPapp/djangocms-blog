# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from copy import deepcopy

from aldryn_apphooks_config.admin import BaseAppHookConfig, ModelAppHookConfig
from cms.admin.placeholderadmin import FrontendEditableAdminMixin, PlaceholderAdminMixin
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from parler.admin import TranslatableAdmin

from .cms_appconfig import BlogConfig
from .forms import PostAdminForm
from .models import BlogCategory, Post
from .settings import get_setting

try:
    from admin_enhancer.admin import EnhancedModelAdminMixin
except ImportError:
    class EnhancedModelAdminMixin(object):
        pass


class BlogCategoryAdmin(EnhancedModelAdminMixin, ModelAppHookConfig, TranslatableAdmin):
    def get_prepopulated_fields(self, request, obj=None):
        app_config_default = self._app_config_select(request, obj)
        if app_config_default is None and request.method == 'GET':
            return {}
        return {'slug': ('name',)}

    class Media:
        css = {
            'all': ('%sdjangocms_blog/css/%s' % (settings.STATIC_URL, 'djangocms_blog_admin.css'),)
        }


class PostAdmin(PlaceholderAdminMixin, FrontendEditableAdminMixin,
                ModelAppHookConfig, TranslatableAdmin):
    form = PostAdminForm
    list_display = ['title', 'author', 'date_published', 'date_published_end']
    date_hierarchy = 'date_published'
    raw_id_fields = ['author']
    frontend_editable_fields = ('title', 'abstract', 'post_text')
    enhance_exclude = ('main_image', 'tags')
    _fieldsets = [
        (None, {
            'fields': [('title', 'categories', 'publish', 'app_config')]
        }),
        ('Info', {
            'fields': (['slug', 'tags'],
                       ('date_published', 'date_published_end', 'enable_comments')),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': (('main_image', 'main_image_thumbnail', 'main_image_full'),),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': [('meta_description', 'meta_title', 'meta_keywords')],
            'classes': ('collapse',)
        }),
    ]

    app_config_values = {
        'default_published': 'publish'
    }

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(PostAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'meta_description':
            original_attrs = field.widget.attrs
            original_attrs['maxlength'] = 160
            field.widget = forms.TextInput(original_attrs)
        elif db_field.name == 'meta_title':
            field.max_length = 70
        return field

    def get_fieldsets(self, request, obj=None):
        app_config_default = self._app_config_select(request, obj)
        if app_config_default is None and request.method == 'GET':
            return super(PostAdmin, self).get_fieldsets(request, obj)
        if not obj:
            config = app_config_default
        else:
            config = obj.app_config

        fsets = deepcopy(self._fieldsets)
        if config:
            if config.use_abstract:
                fsets[0][1]['fields'].append('abstract')
            if not config.use_placeholder:
                fsets[0][1]['fields'].append('post_text')
        else:
            if get_setting('USE_ABSTRACT'):
                fsets[0][1]['fields'].append('abstract')
            if not get_setting('USE_PLACEHOLDER'):
                fsets[0][1]['fields'].append('post_text')
        if get_setting('MULTISITE'):
            fsets[1][1]['fields'][0].append('sites')
        if request.user.is_superuser:
            fsets[1][1]['fields'][0].append('author')
        return fsets

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}

    def save_model(self, request, obj, form, change):
        if not obj.author_id and obj.app_config.set_author:
            if get_setting('AUTHOR_DEFAULT') is True:
                user = request.user
            else:
                user = get_user_model().objects.get(username=get_setting('AUTHOR_DEFAULT'))
            obj.author = user
        super(PostAdmin, self).save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ('%sdjangocms_blog/css/%s' % (settings.STATIC_URL, 'djangocms_blog_admin.css'),)
        }


class BlogConfigAdmin(BaseAppHookConfig, TranslatableAdmin):

    def get_config_fields(self):
        return (
            'app_title', 'config.paginate_by', 'config.set_author', 'config.default_published',
            'config.use_placeholder', 'config.use_abstract',
        )

admin.site.register(BlogCategory, BlogCategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(BlogConfig, BlogConfigAdmin)
