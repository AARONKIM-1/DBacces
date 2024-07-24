from django import forms
from .models import Database, Query
from cryptography.fernet import Fernet
import os

class QueryForm(forms.ModelForm):
    class Meta:
        model = Query
        fields = ['query_text']



class DatabaseForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(render_value=True))

    class Meta:
        model = Database
        fields = '__all__'

    def clean_password(self):
        raw_password = self.cleaned_data['password']
        return raw_password

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['password'].initial = self.instance.decrypt_password()
