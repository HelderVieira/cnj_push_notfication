from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ConteudoLandingPage, CustomUser, Organizacao, Vinculo, ProcessoMonitorados
from .forms import CustomUserCreationForm, CustomAuthenticationForm, OrganizationForm, VinculoForm, ProcessoMonitoradosForm
from django.views.decorators.csrf import csrf_protect

from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

from django.contrib import messages

@login_required
def meus_processos_view(request):
    user = request.user
    # Todos os processos vinculados ao CPF do usuário
    processos_cpf = user.processos_monitorados.all()
    # Organizações que o usuário tem vínculo
    vinculos = Vinculo.objects.filter(usuario=user).select_related('organizacao')
    organizacoes = [v.organizacao for v in vinculos]
    # Dicionário: org_id -> queryset de processos daquela organização
    processos_por_org = {}
    for org in organizacoes:
        processos_por_org[org.id] = org.processos_monitorados.all()
    context = {
        'processos_cpf': processos_cpf,
        'organizacoes': organizacoes,
        'processos_por_org': processos_por_org,
    }
    return render(request, 'website/meus_processos.html', context)

@login_required
def adicionar_processo_view(request):
    user = request.user
    # Organizações onde o usuário é ADMINISTRADOR
    vinculos_admin = Vinculo.objects.filter(usuario=user, tipo=Vinculo.TipoVinculo.ADMINISTRADOR).select_related('organizacao')
    organizacoes_admin = [v.organizacao for v in vinculos_admin]
    vinculo_choices = [(f'user_{user.id}', 'Meu CPF')]
    for org in organizacoes_admin:
        vinculo_choices.append((f'org_{org.id}', org.nome))

    if request.method == 'POST':
        form = ProcessoMonitoradosForm(request.POST, vinculo_choices=vinculo_choices)
        if form.is_valid():
            processo = form.save(commit=False)
            processo.save()
            vinculado = form.cleaned_data['vinculado']
            if vinculado.startswith('user_'):
                user.processos_monitorados.add(processo)
                messages.success(request, 'Processo cadastrado vinculado ao seu CPF.')
            elif vinculado.startswith('org_'):
                org_id = int(vinculado.split('_')[1])
                org = next((o for o in organizacoes_admin if o.id == org_id), None)
                if org:
                    org.processos_monitorados.add(processo)
                    messages.success(request, f'Processo cadastrado vinculado à organização "{org.nome}".')
                else:
                    messages.error(request, 'Organização inválida.')
                    processo.delete()
                    return redirect('adicionar_processo')
            else:
                messages.error(request, 'Vínculo inválido.')
                processo.delete()
                return redirect('adicionar_processo')
            return redirect('meus_processos')
    else:
        form = ProcessoMonitoradosForm(vinculo_choices=vinculo_choices)
    return render(request, 'website/adicionar_processo.html', {'form': form})


def landing_page_view(request):
    conteudo = ConteudoLandingPage.objects.first()
    return render(request, 'website/landing_page.html', {'conteudo': conteudo})

@csrf_protect
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso! Faça login.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'CPF ou senha incorretos.')
        else:
            messages.error(request, 'CPF ou senha inválidos.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('landing_page')

@login_required
def dashboard_view(request):
    return render(request, 'website/dashboard.html')

@login_required
def lista_organizacoes_view(request):
    vinculos = Vinculo.objects.filter(usuario=request.user)
    return render(request, 'organizacoes/lista_organizacoes_usuario.html', {
        'vinculos': vinculos,
    })

@login_required
def cadastro_organizacao_view(request, pk=None):
    if pk:
        org = Organizacao.objects.get(pk=pk)
        vinculo = Vinculo.objects.filter(organizacao=org, usuario=request.user).first()
        is_admin = vinculo and vinculo.tipo == Vinculo.TipoVinculo.ADMINISTRADOR
        if not vinculo:
            messages.error(request, 'Você não tem permissão para acessar esta organização.')
            return redirect('lista_organizacoes')
    else:
        org = None
        is_admin = True  # Criador será admin

    # CRUD de vínculos (apenas admin)
    if request.method == 'POST' and 'vinculo_submit' in request.POST and is_admin:
        vinculo_form = VinculoForm(request.POST)
        if vinculo_form.is_valid():
            try:
                Vinculo.objects.create(
                    organizacao=org,
                    usuario=vinculo_form.cleaned_data['usuario'],
                    tipo=vinculo_form.cleaned_data['tipo']
                )
                messages.success(request, 'Usuário vinculado com sucesso!')
            except Exception as e:
                messages.error(request, f'Erro ao vincular usuário: {e}')
        else:
            messages.error(request, 'Erro ao vincular usuário.')
        return redirect('editar_organizacao', pk=org.pk)

    if request.method == 'POST' and 'remover_vinculo' in request.POST and is_admin:
        vinculo_id = request.POST.get('remover_vinculo')
        try:
            vinculo_remover = Vinculo.objects.get(pk=vinculo_id, organizacao=org)
            if vinculo_remover.usuario != request.user:
                vinculo_remover.delete()
                messages.success(request, 'Vínculo removido com sucesso!')
            else:
                messages.error(request, 'Você não pode remover seu próprio vínculo de administrador.')
        except Exception as e:
            messages.error(request, f'Erro ao remover vínculo: {e}')
        return redirect('editar_organizacao', pk=org.pk)

    if request.method == 'POST' and 'org_submit' in request.POST:
        if not is_admin:
            messages.error(request, 'Você não tem permissão para editar esta organização.')
            return redirect('editar_organizacao', pk=org.pk)
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            organizacao = form.save()
            if not pk:
                Vinculo.objects.create(organizacao=organizacao, usuario=request.user, tipo=Vinculo.TipoVinculo.ADMINISTRADOR)
            messages.success(request, 'Organização salva com sucesso!')
            return redirect('lista_organizacoes')
    else:
        form = OrganizationForm(instance=org)

    vinculo_form = VinculoForm()
    vinculos = Vinculo.objects.filter(organizacao=org) if org else []

    return render(request, 'organizacoes/cadastro_organizacao_usuario.html', {
        'form': form,
        'organizacao': org,
        'is_admin': is_admin,
        'vinculo_form': vinculo_form,
        'vinculos': vinculos,
    })
