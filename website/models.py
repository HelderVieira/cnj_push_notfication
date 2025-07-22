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

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome', 'email']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.nome} ({self.cpf})"

class ConteudoLandingPage(models.Model):
    titulo_principal = models.CharField(max_length=200)
    subtitulo = models.CharField(max_length=300)
    descricao_servico_1 = models.TextField()
    descricao_servico_2 = models.TextField(blank=True, null=True)
    descricao_servico_3 = models.TextField(blank=True, null=True)
    cta_texto = models.CharField('Texto do botão principal', max_length=100, blank=True, null=True)

    def __str__(self):
        return self.titulo_principal
