from django import forms
from .models import Counter

class CounterForm(forms.ModelForm):
    class Meta:
        model = Counter
        fields = ['name', 'counter_id', 'token']