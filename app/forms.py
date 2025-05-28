from django import forms
from .models import Comment,Rating,SatisfactionSurvey

class CommentForm(forms.ModelForm):
    PALABRAS_PROHIBIDAS = ["nefasto", "tonto"]  
    class Meta:
        model = Comment
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("El título debe tener al menos 5 caracteres.")
        for palabra in self.PALABRAS_PROHIBIDAS:
            if palabra in title.lower():
                raise forms.ValidationError(f"El título contiene una palabra inapropiada: '{palabra}'.")
        return title

    def clean_text(self):
        text = self.cleaned_data.get('text')
        for palabra in self.PALABRAS_PROHIBIDAS:
            if palabra in text.lower():
                raise forms.ValidationError(f"El comentario contiene una palabra inapropiada: '{palabra}'.")
        return text


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

class SatisfactionSurveyForm(forms.ModelForm):
    class Meta:
        model = SatisfactionSurvey
        fields = ["rating", "comment"]
        labels = {
            "rating": "Puntuacion",
            "comment": "Comentario",
        }
        widgets = {
            "rating": forms.Select(choices=[(i,i) for i in range(1,6)],
            attrs={"class": "form-select"}
            ),
            "comment": forms.Textarea(attrs={"rows":4, "class": "form-control"}),
        }