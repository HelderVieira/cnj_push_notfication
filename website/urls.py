from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Meus Processos
    path('meus-processos/', views.meus_processos_view, name='meus_processos'),
    path('meus-processos/adicionar/', views.adicionar_processo_view, name='adicionar_processo'),
    path('meus-processos/<int:processo_id>/excluir/', views.excluir_processo_monitorado_view, name='excluir_processo_monitorado'),
    path('meus-processos/<int:processo_id>/excluir/org/<int:org_id>/', views.excluir_processo_monitorado_view, name='excluir_processo_monitorado_org'),
    path('processo/<str:numero_processo>/', views.processo_detail_view, name='processo_detail'),

    # Organização
    path('organizacoes/', views.lista_organizacoes_view, name='lista_organizacoes'),
    path('organizacoes/nova/', views.cadastro_organizacao_view, name='cadastro_organizacao'),
    path('organizacoes/<int:pk>/editar/', views.cadastro_organizacao_view, name='editar_organizacao'),
]

