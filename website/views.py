from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ConteudoLandingPage, CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.views.decorators.csrf import csrf_protect


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
