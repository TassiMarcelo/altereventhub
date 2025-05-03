from django import forms
from .models import Comment,Rating

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['title', 'text', 'rating']
        widgets = {
            'rating': forms.HiddenInput(),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Escribe tu opinión aquí...'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título'
            }),
        }
        labels = {
            'title': 'Título de la calificación*',
            'text': 'Tu reseña(opcional)',
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if text is None or text == '':
            return ''
        return text
