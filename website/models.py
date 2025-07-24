from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, cpf, nome, email, password=None, **extra_fields):
        if not cpf:
            raise ValueError('O CPF é obrigatório')
        if not nome:
            raise ValueError('O nome é obrigatório')
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(cpf=cpf, nome=nome, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cpf, nome, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True.')
        return self.create_user(cpf, nome, email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # Remove o campo username padrão
    cpf_validator = RegexValidator(
        regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        message=_('CPF deve estar no formato 000.000.000-00'),
    )
    cpf = models.CharField(_('CPF'), max_length=14, unique=True, validators=[cpf_validator])
    nome = models.CharField(_('Nome completo'), max_length=255)
    email = models.EmailField(_('E-mail'), unique=True)
    processos_monitorados = models.ManyToManyField('ProcessoMonitorados', related_name='monitorados_por_usuarios', blank=True)

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome', 'email']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nome} ({self.cpf})"

class Organizacao(models.Model):
    cnpj = models.CharField('CNPJ', max_length=14, unique=True)
    nome = models.CharField('Nome da Organização', max_length=255)
    logradouro = models.CharField('Logradouro', max_length=255, blank=True)
    numero = models.CharField('Número', max_length=20, blank=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=2, blank=True)
    cep = models.CharField('CEP', max_length=10, blank=True)
    processos_monitorados = models.ManyToManyField('ProcessoMonitorados', related_name='monitorados_por_organizacao', blank=True)

    def __str__(self):
        return f"{self.nome} ({self.cnpj})"

    def administradores(self):
        return self.vinculos.filter(tipo=Vinculo.TipoVinculo.ADMINISTRADOR)

    def visualizadores(self):
        return self.vinculos.filter(tipo=Vinculo.TipoVinculo.VISUALIZADOR)

class Vinculo(models.Model):
    class TipoVinculo(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        VISUALIZADOR = 'VIEW', 'Visualizador'

    organizacao = models.ForeignKey(Organizacao, related_name='vinculos', on_delete=models.CASCADE)
    usuario = models.ForeignKey('CustomUser', related_name='vinculos', on_delete=models.CASCADE)
    tipo = models.CharField('Tipo de Vínculo', max_length=10, choices=TipoVinculo.choices)

    class Meta:
        unique_together = ('organizacao', 'usuario')
        verbose_name = 'Vínculo'
        verbose_name_plural = 'Vínculos'

    def __str__(self):
        return f"{self.usuario.nome} - {self.organizacao.nome} ({self.get_tipo_display()})"

class ProcessoMonitorados(models.Model):
    numero_processo = models.CharField('Número do Processo', max_length=25)
    orgao_julgador = models.CharField('Órgão Julgador', max_length=255, null=True, blank=True)
    ultima_movimentacao = models.CharField('Última Movimentação Processual', max_length=255, null=True, blank=True)
    data_ultima_movimentacao = models.DateField('Data Última Movimentação', null=True, blank=True)

    def __str__(self):
        return f"{self.numero_processo} - {self.orgao_julgador}"


class ConteudoLandingPage(models.Model):
    titulo_principal = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300)
    descricao_servico_1 = models.TextField()
    descricao_servico_2 = models.TextField(blank=True, null=True)
    descricao_servico_3 = models.TextField(blank=True, null=True)
    cta_texto = models.CharField('Texto do botão principal', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.titulo_principal
