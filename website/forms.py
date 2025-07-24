from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Organizacao, Vinculo, ProcessoMonitorados
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

class ProcessoMonitoradosForm(forms.ModelForm):
    VINCULO_CHOICES = []  # Preenchido dinamicamente na view
    vinculado = forms.ChoiceField(choices=[], label='Vinculado', required=True, widget=forms.Select(attrs={'class': 'form-select'}))

    ORGAO_JULGADOR_CHOICES = [
        # Tribunais Superiores
        ("STF", "SUPREMO TRIBUNAL FEDERAL"),
        ("STJ", "SUPERIOR TRIBUNAL DE JUSTIÇA"),
        ("TST", "TRIBUNAL SUPERIOR DO TRABALHO"),
        ("TSE", "TRIBUNAL SUPERIOR ELEITORAL"),
        ("STM", "SUPERIOR TRIBUNAL MILITAR"),
        # Tribunais Regionais Federais
        ("TRF1", "TRIBUNAL REGIONAL FEDERAL DA 1ª REGIÃO"),
        ("TRF2", "TRIBUNAL REGIONAL FEDERAL DA 2ª REGIÃO"),
        ("TRF3", "TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO"),
        ("TRF4", "TRIBUNAL REGIONAL FEDERAL DA 4ª REGIÃO"),
        ("TRF5", "TRIBUNAL REGIONAL FEDERAL DA 5ª REGIÃO"),
        ("TRF6", "TRIBUNAL REGIONAL FEDERAL DA 6ª REGIÃO"),
        # Tribunais de Justiça Estaduais
        ("TJAC", "TRIBUNAL DE JUSTIÇA DO ESTADO DO ACRE"),
        ("TJAL", "TRIBUNAL DE JUSTIÇA DO ESTADO DE ALAGOAS"),
        ("TJAP", "TRIBUNAL DE JUSTIÇA DO ESTADO DO AMAPÁ"),
        ("TJAM", "TRIBUNAL DE JUSTIÇA DO ESTADO DO AMAZONAS"),
        ("TJBA", "TRIBUNAL DE JUSTIÇA DO ESTADO DA BAHIA"),
        ("TJCE", "TRIBUNAL DE JUSTIÇA DO ESTADO DO CEARÁ"),
        ("TJDFT", "TRIBUNAL DE JUSTIÇA DO DISTRITO FEDERAL E DOS TERRITÓRIOS"),
        ("TJES", "TRIBUNAL DE JUSTIÇA DO ESTADO DO ESPÍRITO SANTO"),
        ("TJGO", "TRIBUNAL DE JUSTIÇA DO ESTADO DE GOIÁS"),
        ("TJMA", "TRIBUNAL DE JUSTIÇA DO ESTADO DO MARANHÃO"),
        ("TJMT", "TRIBUNAL DE JUSTIÇA DO ESTADO DE MATO GROSSO"),
        ("TJMS", "TRIBUNAL DE JUSTIÇA DO ESTADO DE MATO GROSSO DO SUL"),
        ("TJMG", "TRIBUNAL DE JUSTIÇA DO ESTADO DE MINAS GERAIS"),
        ("TJPA", "TRIBUNAL DE JUSTIÇA DO ESTADO DO PARÁ"),
        ("TJPB", "TRIBUNAL DE JUSTIÇA DO ESTADO DA PARAÍBA"),
        ("TJPR", "TRIBUNAL DE JUSTIÇA DO ESTADO DO PARANÁ"),
        ("TJPE", "TRIBUNAL DE JUSTIÇA DO ESTADO DE PERNAMBUCO"),
        ("TJPI", "TRIBUNAL DE JUSTIÇA DO ESTADO DO PIAUÍ"),
        ("TJRJ", "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO"),
        ("TJRN", "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO NORTE"),
        ("TJRS", "TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO SUL"),
        ("TJRO", "TRIBUNAL DE JUSTIÇA DO ESTADO DE RONDÔNIA"),
        ("TJRR", "TRIBUNAL DE JUSTIÇA DO ESTADO DE RORAIMA"),
        ("TJSC", "TRIBUNAL DE JUSTIÇA DO ESTADO DE SANTA CATARINA"),
        ("TJSP", "TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO"),
        ("TJSE", "TRIBUNAL DE JUSTIÇA DO ESTADO DE SERGIPE"),
        ("TJTO", "TRIBUNAL DE JUSTIÇA DO ESTADO DO TOCANTINS"),
        # Tribunais de Justiça Militar Estaduais
        ("TJMMG", "TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DE MINAS GERAIS"),
        ("TJMRS", "TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DO RIO GRANDE DO SUL"),
        ("TJMSP", "TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DE SÃO PAULO")
    ]
    orgao_julgador = forms.ChoiceField(
        choices=ORGAO_JULGADOR_CHOICES,
        initial='TJPB',
        label='Órgão Julgador',
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ProcessoMonitorados
        fields = ['numero_processo', 'orgao_julgador']
        widgets = {
            'numero_processo': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        vinculo_choices = kwargs.pop('vinculo_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['vinculado'].choices = vinculo_choices
        self.fields['numero_processo'].widget.attrs.update(
            {'autofocus': True}
        )

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

