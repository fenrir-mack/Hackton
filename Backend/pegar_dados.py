import os
import json
from datetime import datetime, timedelta

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from manutencao.models import Motor, Medicao

BASE_PATH = r"C:\PASTA DADOS\Usina Alta Mogiana"


# ========================
# DATA
# ========================
def excel_date_to_datetime(excel_date):
    base_date = datetime(1899, 12, 30)
    return base_date + timedelta(days=excel_date)


def converter_data(data_str):
    data_str = data_str.strip()

    try:
        return excel_date_to_datetime(float(data_str.replace(",", ".")))
    except:
        pass

    try:
        return datetime.strptime(data_str, "%d/%m/%y %H:%M:%S")
    except:
        return None


# ========================
# HST9
# ========================
def extrair_hst9(caminho):
    try:
        with open(caminho, "r", encoding="latin-1") as f:
            dados = json.load(f)

        n1 = dados["Bandas"]["Nivel1"][0]
        n2 = dados["Bandas"]["Nivel2"][0]

        if n1 == "0,00" or n2 == "0,00":
            return None, None

        return float(n1.replace(",", ".")), float(n2.replace(",", "."))

    except:
        return None, None


# ========================
# SDAV8
# ========================
def extrair_dados_arquivo(caminho):
    data, rms = None, None

    try:
        with open(caminho, "r", encoding="latin-1") as f:
            for linha in f:
                if linha.startswith("Data="):
                    data = linha.split("=")[1].strip()
                elif linha.startswith("RMS="):
                    rms = linha.split("=")[1].strip()

        return data, rms

    except:
        return None, None


# ========================
# ESCOLHER CONFIG (PRIORIDADE + VALIDAÇÃO)
# ========================
def escolher_configuracao(root, dirs):
    if not dirs:
        return None, None, None

    candidatos = []

    for d in dirs:
        config_path = os.path.join(root, d)
        hst9_path = os.path.join(config_path, f"{d}.HST9")

        if not os.path.exists(hst9_path):
            continue

        nivel1, nivel2 = extrair_hst9(hst9_path)

        # ignora configs inválidas
        if nivel1 is None:
            continue

        nome = d.upper().strip()

        # prioridade
        if nome.startswith("V 2") or nome.startswith("V2"):
            prioridade = 1
        elif nome.startswith("V"):
            prioridade = 2
        else:
            prioridade = 3

        candidatos.append((prioridade, d, nivel1, nivel2))

    if not candidatos:
        return None, None, None

    candidatos.sort(key=lambda x: x[0])

    _, nome, n1, n2 = candidatos[0]

    return nome, n1, n2


# ========================
# CACHE DE MOTORES
# ========================
motor_cache = {}


def get_or_create_motor(usina, sala, sub_sala, nome, configuracao, nivel1, nivel2):
    chave = (usina, sala, sub_sala, nome, configuracao)

    if chave in motor_cache:
        return motor_cache[chave]

    motor, _ = Motor.objects.get_or_create(
        usina=usina,
        sala=sala,
        sub_sala=sub_sala,
        nome=nome,
        configuracao=configuracao,
        defaults={
            "nivel1": nivel1,
            "nivel2": nivel2
        }
    )

    motor_cache[chave] = motor
    return motor


# ========================
# PROCESSAMENTO
# ========================
def processar():
    objetos = []
    usina = os.path.basename(BASE_PATH)

    print(f"🚀 Iniciando: {BASE_PATH}")

    for root, dirs, files in os.walk(BASE_PATH):

        # tenta escolher config dentro da pasta atual
        config_nome, nivel1, nivel2 = escolher_configuracao(root, dirs)

        if not config_nome:
            continue

        config_path = os.path.join(root, config_nome)

        # ========================
        # IDENTIFICA ESTRUTURA
        # ========================
        partes = root.replace(BASE_PATH, "").strip(os.sep).split(os.sep)

        if len(partes) < 2:
            continue

        sala = partes[0]
        nome_motor = partes[-1]

        sub_sala = "/".join(partes[1:-1]) if len(partes) > 2 else None

        print(f"\n📊 Motor encontrado")
        print(f"Sala: {sala}")
        print(f"SubSala: {sub_sala}")
        print(f"Motor: {nome_motor}")
        print(f"Config: {config_nome}")

        # ========================
        # MOTOR
        # ========================
        motor = get_or_create_motor(
            usina, sala, sub_sala, nome_motor, config_nome, nivel1, nivel2
        )

        # ========================
        # SDAV8
        # ========================
        for arquivo in os.listdir(config_path):
            if not arquivo.endswith(".SDAV8"):
                continue

            caminho = os.path.join(config_path, arquivo)

            data, rms = extrair_dados_arquivo(caminho)

            if not data or not rms:
                continue

            data_convertida = converter_data(data)
            if not data_convertida:
                continue

            try:
                rms_val = float(rms.replace(",", "."))
            except:
                continue

            objetos.append(Medicao(
                motor=motor,
                data_arquivo=data_convertida,
                data_convertida=data_convertida,
                rms=rms_val
            ))

    print(f"\n🎯 TOTAL COLETADO: {len(objetos)}")
    return objetos


# ========================
# EXECUÇÃO
# ========================
objetos = processar()

print("\n💾 Salvando em lote...")

BATCH_SIZE = 5000

for i in range(0, len(objetos), BATCH_SIZE):
    lote = objetos[i:i + BATCH_SIZE]

    Medicao.objects.bulk_create(lote, batch_size=BATCH_SIZE)

    print(f"✅ Lote {i} até {i + len(lote)}")

print("🏁 FINALIZADO")