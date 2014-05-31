from django.conf import settings
from django import forms
from django.forms.widgets import HiddenInput
from crits.core.widgets import CalWidget

class AddCommentForm(forms.Form):
    """
    Django form for adding a new Comment.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':6, 'cols':40}))
    parent_date = forms.DateTimeField(widget=HiddenInput, required=False)
    parent_analyst = forms.CharField(widget=HiddenInput, required=False)
    url_key = forms.CharField(widget=HiddenInput(attrs={'class':'no_clear'}))
    #This field helps the server determine if we're on an object's
    #   detail page or the comments aggregation page. Set only on
    #   detail page.
    subscribable = forms.CharField(widget=HiddenInput(attrs={'class':'no_clear'}), required=False)

class JumpToDateForm(forms.Form):
    """
    Django form for finding comments on a specific date.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    date = forms.DateTimeField(widget=CalWidget(format=settings.PY_DATETIME_FORMAT, attrs={'class':'datetimeclass', 'size':'25', 'id':'id_comment_jump_to_date'}), input_formats=settings.PY_FORM_DATETIME_FORMATS)

class InlineCommentForm(forms.Form):
    """
    Django form for adding comments inline.
    """

    error_css_class = 'error'
    required_css_class = 'required'
    comment = forms.CharField(widget=forms.Textarea(attrs={'rows':6, 'cols':40}))
