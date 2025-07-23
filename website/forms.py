from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Organizacao, Vinculo
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

class VinculoForm(forms.ModelForm):
    cpf = forms.CharField(label='CPF do Usuário', max_length=14, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}))

    class Meta:
        model = Vinculo
        fields = ['cpf', 'tipo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        try:
            user = CustomUser.objects.get(cpf=cpf)
        except CustomUser.DoesNotExist:
            raise forms.ValidationError('Usuário com este CPF não encontrado.')
        self.cleaned_data['usuario'] = user
        return cpf

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.usuario = self.cleaned_data['usuario']
        if commit:
            instance.save()
        return instance

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organizacao
        fields = ['nome', 'cnpj', 'logradouro', 'numero', 'complemento', 'bairro', 'cidade', 'estado', 'cep']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'logradouro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        # Adicione validação de formato de CNPJ se necessário
        return cnpj

