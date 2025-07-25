from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson import ObjectId
from django.conf import settings
from django.contrib import messages
from .models import ConteudoLandingPage, CustomUser, Organizacao, Vinculo, ProcessoMonitorados
from .forms import CustomUserCreationForm, CustomAuthenticationForm, OrganizationForm, VinculoForm, ProcessoMonitoradosForm
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.http import Http404
from core.utils.mongodb_connector import find_process_by_number

from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

from django.contrib import messages

@login_required
def meus_processos_view(request):
    user = request.user

    # Tamanho da página, com valor padrão de 10 e validação
    try:
        page_size = int(request.GET.get('page_size', 10))
        if page_size not in [10, 25, 50, 100]:
            page_size = 10
    except (ValueError, TypeError):
        page_size = 10

    # Determina a aba ativa a partir dos parâmetros GET
    active_tab = request.GET.get('tab', 'cpf')
    process_list = []

    if active_tab == 'cpf':
        process_list = user.processos_monitorados.all().order_by('numero_processo')
    elif active_tab.startswith('org_'):
        try:
            org_id = int(active_tab.split('_')[1])
            if Vinculo.objects.filter(usuario=user, organizacao_id=org_id).exists():
                org = Organizacao.objects.get(id=org_id)
                process_list = org.processos_monitorados.all().order_by('numero_processo')
        except (ValueError, Organizacao.DoesNotExist):
            process_list = [] # Em caso de erro, retorna lista vazia

    # Paginação
    paginator = Paginator(process_list, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Se for uma requisição HTMX, retorna apenas o template parcial
    if request.headers.get('HX-Request'):
        return render(request, 'website/partials/_processos_lista.html', {
            'page_obj': page_obj,
            'active_tab': active_tab,
            'page_size': page_size,
        })

    # Para a carga inicial, busca as organizações e renderiza a página completa
    vinculos = Vinculo.objects.filter(usuario=user).select_related('organizacao')
    organizacoes = [v.organizacao for v in vinculos]

    context = {
        'organizacoes': organizacoes,
        'page_obj': page_obj,
        'active_tab': active_tab,
        'page_size': page_size,
    }
    return render(request, 'website/meus_processos.html', context)

@login_required
def notificacoes_view(request):
    user = request.user

    try:
        page_size = int(request.GET.get('page_size', 10))
        if page_size not in [10, 25, 50, 100]:
            page_size = 10
    except (ValueError, TypeError):
        page_size = 10

    active_tab = request.GET.get('tab', 'cpf')
    notificacoes_list = []
    processos_numeros = []

    if active_tab == 'cpf':
        processos_numeros = list(user.processos_monitorados.values_list('numero_processo', flat=True))
    elif active_tab.startswith('org_'):
        try:
            org_id = int(active_tab.split('_')[1])
            if Vinculo.objects.filter(usuario=user, organizacao_id=org_id).exists():
                org = Organizacao.objects.get(id=org_id)
                processos_numeros = list(org.processos_monitorados.values_list('numero_processo', flat=True))
        except (ValueError, Organizacao.DoesNotExist):
            processos_numeros = []

    # Buscar notificações no MongoDB
    notificacoes = []
    if processos_numeros:
        try:
            client = MongoClient(settings.MONGODB_URI)
            db = client[settings.MONGODB_DB_NAME]
            notificacoes_collection = db["notificacoes"]
            notificacoes = list(notificacoes_collection.find({"numero_processo": {"$in": processos_numeros}}).sort("data", -1))
        except (PyMongoError, Exception) as e:
            print(f"Erro ao buscar notificações: {e}")
            notificacoes = []

    paginator = Paginator(notificacoes, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    vinculos = Vinculo.objects.filter(usuario=user).select_related('organizacao')
    organizacoes = [v.organizacao for v in vinculos]

    context = {
        'organizacoes': organizacoes,
        'page_obj': page_obj,
        'active_tab': active_tab,
        'page_size': page_size,
    }
    return render(request, 'website/notificacoes.html', context)


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
def excluir_processo_monitorado_view(request, processo_id, org_id=None):
    """
    Remove um processo da lista de monitorados do usuário e, se org_id for informado e o usuário for admin,
    também remove da organização.
    """
    from django.http import HttpResponseForbidden
    user = request.user
    try:
        processo = ProcessoMonitorados.objects.get(id=processo_id)
    except ProcessoMonitorados.DoesNotExist:
        messages.error(request, 'Processo não encontrado.')
        return redirect('meus_processos')

    if org_id:
        # Tentativa de remover da organização
        try:
            org = Organizacao.objects.get(id=org_id)
        except Organizacao.DoesNotExist:
            messages.error(request, 'Organização não encontrada.')
            return redirect('meus_processos')
        # Verifica se usuário é admin
        vinculo_admin = Vinculo.objects.filter(usuario=user, organizacao=org, tipo=Vinculo.TipoVinculo.ADMINISTRADOR).exists()
        if not vinculo_admin:
            return HttpResponseForbidden('Você não tem permissão para remover processos desta organização.')
        org.processos_monitorados.remove(processo)
        messages.success(request, 'Processo removido da organização com sucesso!')
    else:
        # Remover do CPF do usuário
        user.processos_monitorados.remove(processo)
        messages.success(request, 'Processo removido da sua lista com sucesso!')

    return redirect('meus_processos')

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


def formatar_numero_processo(numero_processo):
    """
    Recebe um número de processo e retorna apenas os algarísmos numéricos.
    """
    return ''.join(filter(str.isdigit, numero_processo))


def get_movimentacoes_by_processo_id(processo_id):
    """
    Busca as movimentações de um processo pelo seu ID do MongoDB.
    """
    try:
        client = MongoClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB_NAME]
        movimentacoes_collection = db["movimentacoes"]

        movimentacoes = list(movimentacoes_collection.find({"processo_id": processo_id}))
        
        return movimentacoes
    except (PyMongoError, Exception) as e:
        print(f"Erro ao buscar movimentações: {e}")
        return []

@login_required
def processo_detail_view(request, numero_processo):
    """
    Exibe os detalhes de um processo consultado no MongoDB.
    """
    processo_data = find_process_by_number(formatar_numero_processo(numero_processo))
    if not processo_data:
        raise Http404("Processo não encontrado no banco de dados.")

    if '_id' in processo_data:
        processo_data['_id'] = str(processo_data['_id'])

    movimentacoes = []
    if processo_data and '_id' in processo_data:
        movimentacoes = get_movimentacoes_by_processo_id(processo_data['_id'])

    context = {
        'processo': processo_data,
        'numero_processo': numero_processo,
        'movimentacoes': movimentacoes
    }
    return render(request, 'website/processo_detail.html', context)
