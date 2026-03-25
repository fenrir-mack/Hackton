from django.urls import path
from . import views

app_name = 'manutencao'  # ⬅️ required for reverse_lazy to work

urlpatterns = [
    path('relatorio/', views.relatorios_view, name='relatorio'),
    path('graficos/', views.graficos_view, name='graficos'),
    path('visao_geral/', views.visao_geral_view, name='visao_geral'),
    path('kanban/', views.kanban_view, name='kanban'),
]
