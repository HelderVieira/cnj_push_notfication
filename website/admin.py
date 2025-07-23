from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ConteudoLandingPage, Organizacao, Vinculo

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('cpf', 'nome', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('cpf', 'nome', 'email')
    ordering = ('cpf',)
    fieldsets = (
        (None, {'fields': ('cpf', 'password')}),
        ('Informações pessoais', {'fields': ('nome', 'email')}),
        ('Permissões', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Datas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('cpf', 'nome', 'email', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )

@admin.register(ConteudoLandingPage)
class ConteudoLandingPageAdmin(admin.ModelAdmin):
    list_display = ('titulo_principal', 'subtitulo')

class VinculoInline(admin.TabularInline):
    model = Vinculo
    extra = 1

@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'cidade', 'estado')
    search_fields = ('nome', 'cnpj')
    inlines = [VinculoInline]

@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'organizacao', 'tipo')
    list_filter = ('tipo', 'organizacao')
    search_fields = ('usuario__nome', 'usuario__cpf', 'organizacao__nome', 'organizacao__cnpj')
