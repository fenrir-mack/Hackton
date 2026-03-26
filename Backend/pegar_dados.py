import os
import json
from datetime import datetime, timedelta

BASE_PATH = r"C:\PASTA DADOS\Usina Alta Mogiana"

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
# ========================
# DATA
# ========================
def excel_date_to_datetime(excel_date):
    base_date = datetime(1899, 12, 30)
    return base_date + timedelta(days=excel_date)


def converter_data(data_str):
    data_str = data_str.strip()

    # tenta excel
    try:
        return excel_date_to_datetime(float(data_str.replace(",", ".")))
    except:
        pass

    # tenta texto
    try:
        return datetime.strptime(data_str, "%d/%m/%y %H:%M:%S")
    except:
        pass

    print(f"❌ Data inválida: {data_str}")
    return None


# ========================
# HST9
# ========================
def extrair_hst9(caminho_pasta):
    nome = os.path.basename(caminho_pasta)
    caminho = os.path.join(caminho_pasta, f"{nome}.HST9")

    if not os.path.exists(caminho):
        print(f"⚠️ Sem HST9: {caminho}")
        return None, None

    try:
        with open(caminho, "r", encoding="latin-1") as f:
            dados = json.load(f)

        n1 = dados["Bandas"]["Nivel1"][0]
        n2 = dados["Bandas"]["Nivel2"][0]

        print(f"📊 HST9 -> N1={n1} | N2={n2}")

        if n1 == "0,00" or n2 == "0,00":
            print("⛔ Ignorado (nível zero)")
            return None, None

        return float(n1.replace(",", ".")), float(n2.replace(",", "."))

    except Exception as e:
        print(f"❌ Erro HST9: {e}")
        return None, None


# ========================
# SDAV8
# ========================
def extrair_dados_arquivo(caminho):
    data = None
    rms = None

    try:
        with open(caminho, "r", encoding="latin-1") as f:
            for linha in f:
                if linha.startswith("Data="):
                    data = linha.split("=")[1].strip()
                elif linha.startswith("RMS="):
                    rms = linha.split("=")[1].strip()

        return data, rms

    except Exception as e:
        print(f"❌ Erro SDAV8: {caminho} | {e}")
        return None, None


# ========================
# PROCESSAMENTO
# ========================
def processar():
    resultados = []

    print(f"\n🚀 Iniciando: {BASE_PATH}")

    for sala in os.listdir(BASE_PATH):
        caminho_sala = os.path.join(BASE_PATH, sala)

        if not os.path.isdir(caminho_sala):
            continue

        print(f"\n📂 Sala: {sala}")

        # percorre tudo dentro da sala
        for root, dirs, files in os.walk(caminho_sala):

            # 🔥 detecta configuração (onde existe HST9)
            hst9_files = [f for f in files if f.endswith(".HST9")]

            if not hst9_files:
                continue

            config_path = root
            config = os.path.basename(config_path)

            # sobe níveis
            partes = config_path.replace(caminho_sala, "").strip(os.sep).split(os.sep)

            # 🧠 interpretação dinâmica
            if len(partes) == 2:
                # SALA/MOTOR/CONFIG
                sub_sala = None
                motor = partes[0]

            elif len(partes) >= 3:
                # SALA/SUBSALA/MOTOR/CONFIG
                sub_sala = partes[0]
                motor = partes[1]

            else:
                print(f"⚠️ Estrutura desconhecida: {config_path}")
                continue

            print(f"\n📊 CONFIG ENCONTRADA")
            print(f"SubSala: {sub_sala}")
            print(f"Motor: {motor}")
            print(f"Config: {config}")

            # 🔍 extrai HST9
            nivel1, nivel2 = extrair_hst9(config_path)

            if nivel1 is None:
                continue

            # 📄 arquivos SDAV8
            for arquivo in files:
                if not arquivo.endswith(".SDAV8"):
                    continue

                caminho_arquivo = os.path.join(config_path, arquivo)

                data, rms = extrair_dados_arquivo(caminho_arquivo)

                if not data or not rms:
                    continue

                data_convertida = converter_data(data)

                if not data_convertida:
                    continue

                try:
                    data_float = float(data.replace(",", "."))
                except:
                    data_float = None

                try:
                    rms_val = float(rms.replace(",", "."))
                except:
                    continue

                registro = {
                    "usina": os.path.basename(BASE_PATH),
                    "sala": sala,
                    "sub_sala": sub_sala,
                    "motor": motor,
                    "configuracao": config,
                    "arquivo": arquivo,
                    "data_arquivo": data_float,
                    "data_convertida": data_convertida,
                    "rms": rms_val,
                    "nivel1": nivel1,
                    "nivel2": nivel2
                }

                print(f"💾 {registro}")

                resultados.append(registro)

    print(f"\n🎯 TOTAL COLETADO: {len(resultados)}")
    return resultados

# ========================
# EXECUÇÃO
# ========================
dados = processar()


# ========================
# SALVAR NO DJANGO
# ========================
from manutencao.models import Medicao

print("\n💾 Salvando em lote...")

objetos = []

for d in dados:
    objetos.append(Medicao(
        usina=d["usina"],
        sala=d["sala"],
        sub_sala=d["sub_sala"],
        motor=d["motor"],
        configuracao=d["configuracao"],
        arquivo=d["arquivo"],
        data_arquivo=d["data_arquivo"],
        data_convertida=d["data_convertida"],
        rms=d["rms"],
        nivel1=d["nivel1"],
        nivel2=d["nivel2"]
    ))

# 🔥 salva de 5k em 5k (evita estourar memória)
BATCH_SIZE = 5000

for i in range(0, len(objetos), BATCH_SIZE):
    lote = objetos[i:i + BATCH_SIZE]

    Medicao.objects.bulk_create(lote, batch_size=BATCH_SIZE)

    print(f"✅ Salvo lote {i} até {i + len(lote)}")

print("🏁 FINALIZADO")