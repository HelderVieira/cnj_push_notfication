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
        ("STF", "STF - SUPREMO TRIBUNAL FEDERAL"),
        ("STJ", "STJ - SUPERIOR TRIBUNAL DE JUSTIÇA"),
        ("TST", "TST - TRIBUNAL SUPERIOR DO TRABALHO"),
        ("TSE", "TSE - TRIBUNAL SUPERIOR ELEITORAL"),
        ("STM", "STM - SUPERIOR TRIBUNAL MILITAR"),

        # Tribunais Regionais Federais
        ("TRF1", "TRF1 - TRIBUNAL REGIONAL FEDERAL DA 1ª REGIÃO"),
        ("TRF2", "TRF2 - TRIBUNAL REGIONAL FEDERAL DA 2ª REGIÃO"),
        ("TRF3", "TRF3 - TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO"),
        ("TRF4", "TRF4 - TRIBUNAL REGIONAL FEDERAL DA 4ª REGIÃO"),
        ("TRF5", "TRF5 - TRIBUNAL REGIONAL FEDERAL DA 5ª REGIÃO"),
        ("TRF6", "TRF6 - TRIBUNAL REGIONAL FEDERAL DA 6ª REGIÃO"),

        # Tribunais Regionais do Trabalho
        ("TRT1", "TRT1 - TRIBUNAL REGIONAL DO TRABALHO DA 1ª REGIÃO (RJ)"),
        ("TRT2", "TRT2 - TRIBUNAL REGIONAL DO TRABALHO DA 2ª REGIÃO (SP)"),
        ("TRT3", "TRT3 - TRIBUNAL REGIONAL DO TRABALHO DA 3ª REGIÃO (MG)"),
        ("TRT4", "TRT4 - TRIBUNAL REGIONAL DO TRABALHO DA 4ª REGIÃO (RS)"),
        ("TRT5", "TRT5 - TRIBUNAL REGIONAL DO TRABALHO DA 5ª REGIÃO (BA)"),
        ("TRT6", "TRT6 - TRIBUNAL REGIONAL DO TRABALHO DA 6ª REGIÃO (PE)"),
        ("TRT7", "TRT7 - TRIBUNAL REGIONAL DO TRABALHO DA 7ª REGIÃO (CE)"),
        ("TRT8", "TRT8 - TRIBUNAL REGIONAL DO TRABALHO DA 8ª REGIÃO (PA/AP)"),
        ("TRT9", "TRT9 - TRIBUNAL REGIONAL DO TRABALHO DA 9ª REGIÃO (PR)"),
        ("TRT10", "TRT10 - TRIBUNAL REGIONAL DO TRABALHO DA 10ª REGIÃO (DF/TO)"),
        ("TRT11", "TRT11 - TRIBUNAL REGIONAL DO TRABALHO DA 11ª REGIÃO (AM/RR)"),
        ("TRT12", "TRT12 - TRIBUNAL REGIONAL DO TRABALHO DA 12ª REGIÃO (SC)"),
        ("TRT13", "TRT13 - TRIBUNAL REGIONAL DO TRABALHO DA 13ª REGIÃO (PB)"),
        ("TRT14", "TRT14 - TRIBUNAL REGIONAL DO TRABALHO DA 14ª REGIÃO (RO/AC)"),
        ("TRT15", "TRT15 - TRIBUNAL REGIONAL DO TRABALHO DA 15ª REGIÃO (CAMPINAS/SP)"),
        ("TRT16", "TRT16 - TRIBUNAL REGIONAL DO TRABALHO DA 16ª REGIÃO (MA)"),
        ("TRT17", "TRT17 - TRIBUNAL REGIONAL DO TRABALHO DA 17ª REGIÃO (ES)"),
        ("TRT18", "TRT18 - TRIBUNAL REGIONAL DO TRABALHO DA 18ª REGIÃO (GO)"),
        ("TRT19", "TRT19 - TRIBUNAL REGIONAL DO TRABALHO DA 19ª REGIÃO (AL)"),
        ("TRT20", "TRT20 - TRIBUNAL REGIONAL DO TRABALHO DA 20ª REGIÃO (SE)"),
        ("TRT21", "TRT21 - TRIBUNAL REGIONAL DO TRABALHO DA 21ª REGIÃO (RN)"),
        ("TRT22", "TRT22 - TRIBUNAL REGIONAL DO TRABALHO DA 22ª REGIÃO (PI)"),
        ("TRT23", "TRT23 - TRIBUNAL REGIONAL DO TRABALHO DA 23ª REGIÃO (MT)"),
        ("TRT24", "TRT24 - TRIBUNAL REGIONAL DO TRABALHO DA 24ª REGIÃO (MS)"),

        # Tribunais Regionais Eleitorais
        ("TREAC", "TREAC - TRIBUNAL REGIONAL ELEITORAL DO ACRE"),
        ("TREAL", "TREAL - TRIBUNAL REGIONAL ELEITORAL DE ALAGOAS"),
        ("TREAP", "TREAP - TRIBUNAL REGIONAL ELEITORAL DO AMAPÁ"),
        ("TREAM", "TREAM - TRIBUNAL REGIONAL ELEITORAL DO AMAZONAS"),
        ("TREBA", "TREBA - TRIBUNAL REGIONAL ELEITORAL DA BAHIA"),
        ("TRECE", "TRECE - TRIBUNAL REGIONAL ELEITORAL DO CEARÁ"),
        ("TREDF", "TREDF - TRIBUNAL REGIONAL ELEITORAL DO DISTRITO FEDERAL"),
        ("TREES", "TREES - TRIBUNAL REGIONAL ELEITORAL DO ESPÍRITO SANTO"),
        ("TREGO", "TREGO - TRIBUNAL REGIONAL ELEITORAL DE GOIÁS"),
        ("TREMA", "TREMA - TRIBUNAL REGIONAL ELEITORAL DO MARANHÃO"),
        ("TREMT", "TREMT - TRIBUNAL REGIONAL ELEITORAL DE MATO GROSSO"),
        ("TREMS", "TREMS - TRIBUNAL REGIONAL ELEITORAL DE MATO GROSSO DO SUL"),
        ("TREMG", "TREMG - TRIBUNAL REGIONAL ELEITORAL DE MINAS GERAIS"),
        ("TREPA", "TREPA - TRIBUNAL REGIONAL ELEITORAL DO PARÁ"),
        ("TREPB", "TREPB - TRIBUNAL REGIONAL ELEITORAL DA PARAÍBA"),
        ("TREPR", "TREPR - TRIBUNAL REGIONAL ELEITORAL DO PARANÁ"),
        ("TREPE", "TREPE - TRIBUNAL REGIONAL ELEITORAL DE PERNAMBUCO"),
        ("TREPI", "TREPI - TRIBUNAL REGIONAL ELEITORAL DO PIAUÍ"),
        ("TRERJ", "TRERJ - TRIBUNAL REGIONAL ELEITORAL DO RIO DE JANEIRO"),
        ("TRERN", "TRERN - TRIBUNAL REGIONAL ELEITORAL DO RIO GRANDE DO NORTE"),
        ("TRERS", "TRERS - TRIBUNAL REGIONAL ELEITORAL DO RIO GRANDE DO SUL"),
        ("TRERO", "TRERO - TRIBUNAL REGIONAL ELEITORAL DE RONDÔNIA"),
        ("TRERR", "TRERR - TRIBUNAL REGIONAL ELEITORAL DE RORAIMA"),
        ("TRESC", "TRESC - TRIBUNAL REGIONAL ELEITORAL DE SANTA CATARINA"),
        ("TRESP", "TRESP - TRIBUNAL REGIONAL ELEITORAL DE SÃO PAULO"),
        ("TRESE", "TRESE - TRIBUNAL REGIONAL ELEITORAL DE SERGIPE"),
        ("TRETO", "TRETO - TRIBUNAL REGIONAL ELEITORAL DO TOCANTINS"),

        # Tribunais de Justiça Estaduais
        ("TJAC", "TJAC - TRIBUNAL DE JUSTIÇA DO ESTADO DO ACRE"),
        ("TJAL", "TJAL - TRIBUNAL DE JUSTIÇA DO ESTADO DE ALAGOAS"),
        ("TJAP", "TJAP - TRIBUNAL DE JUSTIÇA DO ESTADO DO AMAPÁ"),
        ("TJAM", "TJAM - TRIBUNAL DE JUSTIÇA DO ESTADO DO AMAZONAS"),
        ("TJBA", "TJBA - TRIBUNAL DE JUSTIÇA DO ESTADO DA BAHIA"),
        ("TJCE", "TJCE - TRIBUNAL DE JUSTIÇA DO ESTADO DO CEARÁ"),
        ("TJDFT", "TJDFT - TRIBUNAL DE JUSTIÇA DO DISTRITO FEDERAL E DOS TERRITÓRIOS"),
        ("TJES", "TJES - TRIBUNAL DE JUSTIÇA DO ESTADO DO ESPÍRITO SANTO"),
        ("TJGO", "TJGO - TRIBUNAL DE JUSTIÇA DO ESTADO DE GOIÁS"),
        ("TJMA", "TJMA - TRIBUNAL DE JUSTIÇA DO ESTADO DO MARANHÃO"),
        ("TJMT", "TJMT - TRIBUNAL DE JUSTIÇA DO ESTADO DE MATO GROSSO"),
        ("TJMS", "TJMS - TRIBUNAL DE JUSTIÇA DO ESTADO DE MATO GROSSO DO SUL"),
        ("TJMG", "TJMG - TRIBUNAL DE JUSTIÇA DO ESTADO DE MINAS GERAIS"),
        ("TJPA", "TJPA - TRIBUNAL DE JUSTIÇA DO ESTADO DO PARÁ"),
        ("TJPB", "TJPB - TRIBUNAL DE JUSTIÇA DO ESTADO DA PARAÍBA"),
        ("TJPR", "TJPR - TRIBUNAL DE JUSTIÇA DO ESTADO DO PARANÁ"),
        ("TJPE", "TJPE - TRIBUNAL DE JUSTIÇA DO ESTADO DE PERNAMBUCO"),
        ("TJPI", "TJPI - TRIBUNAL DE JUSTIÇA DO ESTADO DO PIAUÍ"),
        ("TJRJ", "TJRJ - TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO DE JANEIRO"),
        ("TJRN", "TJRN - TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO NORTE"),
        ("TJRS", "TJRS - TRIBUNAL DE JUSTIÇA DO ESTADO DO RIO GRANDE DO SUL"),
        ("TJRO", "TJRO - TRIBUNAL DE JUSTIÇA DO ESTADO DE RONDÔNIA"),
        ("TJRR", "TJRR - TRIBUNAL DE JUSTIÇA DO ESTADO DE RORAIMA"),
        ("TJSC", "TJSC - TRIBUNAL DE JUSTIÇA DO ESTADO DE SANTA CATARINA"),
        ("TJSP", "TJSP - TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO"),
        ("TJSE", "TJSE - TRIBUNAL DE JUSTIÇA DO ESTADO DE SERGIPE"),
        ("TJTO", "TJTO - TRIBUNAL DE JUSTIÇA DO ESTADO DO TOCANTINS"),

        # Tribunais de Justiça Militar Estaduais
        ("TJMMG", "TJMMG - TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DE MINAS GERAIS"),
        ("TJMRS", "TJMRS - TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DO RIO GRANDE DO SUL"),
        ("TJMSP", "TJMSP - TRIBUNAL DE JUSTIÇA MILITAR DO ESTADO DE SÃO PAULO")
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

