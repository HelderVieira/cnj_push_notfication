from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.core.validators import RegexValidator

class CustomUserCreationForm(UserCreationForm):
    cpf = forms.CharField(
        label='CPF',
        max_length=14,
        validators=[RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', message='CPF deve estar no formato 000.000.000-00')]
    )
    nome = forms.CharField(label='Nome completo', max_length=255)
    email = forms.EmailField(label='E-mail')

    class Meta:
        model = CustomUser
        fields = ('nome', 'email', 'cpf', 'password1', 'password2')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='CPF',
        max_length=14,
        widget=forms.TextInput(attrs={'autofocus': True, 'placeholder': '000.000.000-00'}),
        validators=[RegexValidator(regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', message='CPF deve estar no formato 000.000.000-00')]
    )
    # Não precisa de campo cpf separado, pois o USERNAME_FIELD do modelo é cpf
