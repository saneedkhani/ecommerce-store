from django import forms


class BootstrapFormMixin:
    """Give every field the right Bootstrap 5 CSS class so templates can render forms cleanly."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                css = 'form-check-input'
            elif isinstance(widget, forms.Select):
                css = 'form-select'
            else:
                css = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()
            if field.label and not isinstance(widget, (forms.CheckboxInput, forms.RadioSelect, forms.Select, forms.FileInput)):
                widget.attrs.setdefault('placeholder', field.label)
