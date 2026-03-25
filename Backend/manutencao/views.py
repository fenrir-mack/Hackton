from django.shortcuts import render


def relatorios_view(request):
    return render(request, 'manutencao/relatorios.html')

def graficos_view(request):
    return render(request, 'manutencao/graficos.html')

def visao_geral_view(request):
    return render(request, "manutencao/visao_geral.html")

def kanban_view(request):
    return render(request, 'manutencao/kanban.html')