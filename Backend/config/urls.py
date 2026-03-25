from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.views.generic.base import RedirectView
#teste
urlpatterns = [
    path('admin/', admin.site.urls),
    path('manutencao/', include('manutencao.urls')),

    path('relatorio/', RedirectView.as_view(url=reverse_lazy('manutencao:relatorios'), permanent=False)),
    path('graficos/', RedirectView.as_view(url=reverse_lazy('manutencao:graficos'), permanent=False)),
    path('visao_geral/', RedirectView.as_view(url=reverse_lazy('manutencao:visao_geral'), permanent=False)),
    path('kanban/', RedirectView.as_view(url=reverse_lazy('manutencao:kanban'), permanent=False)),
]