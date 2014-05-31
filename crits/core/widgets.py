from django import forms
from django.forms.widgets import Select
from django.forms.fields import ChoiceField
from itertools import chain
from django.utils.encoding import force_unicode, smart_unicode
from django.utils.html import escape, conditional_escape

class CalWidget(forms.DateTimeInput):
    """
    Calendar Widget.
    """

    class Media:
        css = {
            }
        js = (
            '/js/datetimewidget.js',
            )

class ExtendedSelect(Select):
    """
    A subclass of Select that adds the possibility to define additional
    properties on options.

    It works as Select, except that the "choices" parameter takes a list of 3
    elements tuples containing the (value, label, attrs), where attrs is a dict
    containing the additional attributes of the option.

    Source credit: http://stackoverflow.com/questions/965082/option-level-control-of-select-inputs-using-django-forms-api with updates based on Django 1.4.0.
    """
    #TODO: probably want to add an option_attrs attribute and use that instead of using a three-tuple for choices.
    #   We need to do this so that calling is_valid will still work. (Currently it fails because there are too
    #   many values to unpack.)

    def render_options(self, choices, selected_choices):
        def render_option(option_value, option_label, attrs):
            option_value = force_unicode(option_value)
            if option_value in selected_choices:
                selected_html = u' selected="selected"'
                if not self.allow_multiple_selected:
                    #Only allow for a single selection.
                    selected_choices.remove(option_value)
            else:
                selected_html = ''
            attrs_html = []
            for k, v in attrs.items():
                if isinstance(v, list):
                    #emulate JavaScript behavior casting list to string
                    v = ','.join(v)
                attrs_html.append('%s="%s"' % (k, escape(v)))
            if attrs_html:
                attrs_html = " " + " ".join(attrs_html)
            else:
                attrs_html = ""
            return u'<option value="%s"%s%s>%s</option>' % (
                escape(option_value), selected_html, attrs_html,
                conditional_escape(force_unicode(option_label)))
        # Normalize to strings.
        selected_choices = set(force_unicode(v) for v in selected_choices)
        output = []
        for option_value, option_label, option_attrs in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(render_option(*option))
                output.append(u'</optgroup>')
            else:
                output.append(render_option(option_value, option_label,
                    option_attrs))
        return u'\n'.join(output)

class ExtendedChoiceField(ChoiceField):
    """
    A subclass of ChoiceField that provides validation for an ExtendedSelect
    field.

    There are two differences between this class and the ChoiceField class
    defined in django.forms.fields.
        1) The default widget is changed from Select to ExtendedSelect
        2) In order to prevent a "ValueError: too many values to unpack" in
            valid_value,
                for k, v in self.choices
           is replaced with
                for k, v, attrs in self.choices
    """

    widget = ExtendedSelect

    def valid_value(self, value):
        "Check to see if the provided value is a valid choice"
        for k, v, attrs in self.choices:
            if isinstance(v, (list, tuple)):
                # This is an optgroup, so look inside the group for options
                for k2, v2 in v:
                    if value == smart_unicode(k2):
                        return True
            else:
                if value == smart_unicode(k):
                    return True
        return False
