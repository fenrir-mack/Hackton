from django.db.models import Min,Q
from collections import defaultdict
from django.shortcuts import render
from manutencao.models import Motor, Medicao, ResultadoMotor

#para testar algum em especifico, tem que ter base de dados em C:Nome que quiser/Ausina
def buscar_motor_por_path(path):
    partes = path.split('\\')

    usina = partes[2]
    sala = partes[3]

    # motor é sempre a última pasta
    motor_nome = partes[-1]

    # tudo entre sala e motor é sub_sala (pode ter várias)
    if len(partes) > 5:
        sub_sala = "/".join(partes[4:-1])
    else:
        sub_sala = None

    print("🔍 Buscando:")
    print(usina, sala, sub_sala, motor_nome)

    return Motor.objects.filter(
        usina=usina,
        sala=sala,
        sub_sala=sub_sala,
        nome=motor_nome
    ).first()

#algoritimo para limpar e ver se precisa ser calculado o valor
def limpar_rms(lista, nivel1, resultado_motor):
    total = len(lista)

    for i in range(total):
        atual = lista[i]['rms']

        if atual == 0:
            continue

        if atual > nivel1:

            for j in range(1, 3):
                if i + j >= total:
                    continue

                futuro = lista[i + j]['rms']
                queda = (atual - futuro) / atual

                if queda >= 0.3:

                    pontos_restantes = total - (i + j)

                    if pontos_restantes >= max(int(total * 0.2), 6):
                        return lista[i + j:]

                    else:
                        resultado_motor.manutencao_recente = True
                        resultado_motor.save()
                        return lista

    return lista

#se ja passou do por isso manutenção direto
def verificar_limite2(lista, nivel2, resultado_motor):
    for p in lista:
        if p['rms'] >= nivel2:
            resultado_motor.ja_bateu_no_limite = True
            resultado_motor.save()
            return True

    return False
def relatorios_view(request):
    return render(request, 'manutencao/relatorios.html')

def graficos_view(request):
    return render(request, 'manutencao/graficos.html')


def visao_geral_view(request):
    path = r"C:\PASTA DADOS\Usina Alta Mogiana\EXCA - Redutores Moenda B\11- PENEIRA ROTATIVA N°2 LADO CALD\1H ENT MOTOR"

    # 1️⃣ buscar motor
    motor = buscar_motor_por_path(path)

    # 2️⃣ pegar dados
    dados = (
        Medicao.objects
        .filter(motor=motor)
        .order_by('data_convertida')
    )

    lista = []

    for d in dados:
        lista.append({
            "data": d.data_convertida,
            "rms": d.rms
        })

    # 3️⃣ resultado motor
    resultado_motor, _ = ResultadoMotor.objects.get_or_create(motor=motor)

    # 4️⃣ limpar dados
    lista_limpa = limpar_rms(lista, motor.nivel1, resultado_motor)

    # 5️⃣ verificar limite 2
    verificar_limite2(lista_limpa, motor.nivel2, resultado_motor)

    # 6️⃣ enviar para o template
    return render(request, 'manutencao/visao_geral.html', {
        'motor': motor,
        'dados': lista_limpa
    })

def kanban_view(request):
    return render(request, 'manutencao/kanban.html')