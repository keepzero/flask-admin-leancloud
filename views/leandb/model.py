# coding: utf-8

from flask_admin.model import BaseModelView
from flask_admin.helpers import get_form_data
from flask_admin.actions import action
from flask_admin.babel import ngettext, lazy_gettext
from flask import flash
from wtforms import fields
from leancloud import Query, Object, File
from jinja2 import Markup
from datetime import datetime, date


class LeanDb(object):
    def __init__(self, coll):
        self.Class = Object.extend(coll)

    def query(self):
        return Query(self.Class)

    @classmethod
    def new_query(cls, classname):
        return Query(Object.extend(classname))

    @classmethod
    def new_class(cls, classname):
        return Object.extend(classname)


class ModelView(BaseModelView):
    """LeanCloud Model"""

    column_filters = None
    details_modal = True
    create_modal = True
    edit_modal = True
    form_image_width = 150
    form_image_height = 150

    def __init__(self, coll,
                 name=None, category=None, endpoint=None, url=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
        super(ModelView, self).__init__(None, name, category, endpoint, url,
                                        menu_class_name=menu_class_name,
                                        menu_icon_type=menu_icon_type,
                                        menu_icon_value=menu_icon_value)
        self.coll = coll

    def get_pk_value(self, model):
        return model.id

    def scaffold_list_columns(self):
        raise NotImplementedError()

    def scaffold_sortable_columns(self):
        return []

    def init_search(self):
        return False

    def scaffold_filters(self, name):
        raise NotImplementedError()

    def scaffold_form(self):
        raise NotImplementedError()

    def _get_field_value(self, model, name):
        value = model.get(name)
        if isinstance(value, File):
            if value._type.startswith('image/'):
                return Markup("<a href='%s'><img src='%s'/></a>" % (
                    value.url, value.get_thumbnail_url(width=self.form_image_width, height=self.form_image_height)))
            else:
                return Markup("<a href='%s'>%s</a>" % (value.url, value.name))
        return value

    def get_list(self, page, sort_field, sort_desc, search, filters, page_size=None):
        query = self.coll.query()
        count = query.count()

        if page_size is None:
            page_size = self.page_size
        query.skip(page * page_size)
        query.ascending('create_at')
        query.limit(page_size)
        results = query.find()

        return count, results

    def get_one(self, id):
        return self.coll.query().get(id)

    def edit_form(self, obj):
        cols = {}
        for col in set(self.column_list + self.column_details_list):
            cols[col] = obj.get(col)
        return self._edit_form_class(get_form_data(), **cols)

    def create_model(self, form):
        model = self.coll.Class()
        model.set(form.data)
        self._on_model_change(form, model, True)
        model.save()
        return model

    def update_model(self, form, model):
        model.set(form.data)
        self._on_model_change(form, model, False)
        model.save()
        return True

    def delete_model(self, model):
        model.destroy()
        return True

    def is_valid_filter(self, filter):
        return True

    @action('delete', lazy_gettext('Delete'), lazy_gettext('Are you sure to delete selected row?'))
    def action_delete(self, ids):
        count = 0
        for pk in ids:
            self.get_one(pk).destroy()
            count += 1
        flash(ngettext('Record was successfully deleted.',
                       '%(count)s records were successfully deleted.',
                       count,
                       count=count))
