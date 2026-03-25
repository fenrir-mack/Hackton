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
        print(f"Conteúdo: {os.listdir(caminho_sala)}")

        for subsala in os.listdir(caminho_sala):
            caminho_subsala = os.path.join(caminho_sala, subsala)

            if not os.path.isdir(caminho_subsala):
                continue

            print(f"\n📁 SubSala: {subsala}")

            for motor in os.listdir(caminho_subsala):
                caminho_motor = os.path.join(caminho_subsala, motor)

                if not os.path.isdir(caminho_motor):
                    continue

                print(f"⚙️ Motor: {motor}")

                for config in os.listdir(caminho_motor):
                    caminho_config = os.path.join(caminho_motor, config)

                    if not os.path.isdir(caminho_config):
                        continue

                    print(f"📊 Config: {config}")

                    nivel1, nivel2 = extrair_hst9(caminho_config)

                    if nivel1 is None:
                        continue

                    print("✅ HST9 válido")

                    for arquivo in os.listdir(caminho_config):
                        if not arquivo.endswith(".SDAV8"):
                            continue

                        caminho_arquivo = os.path.join(caminho_config, arquivo)

                        print(f"📄 Lendo: {arquivo}")

                        data, rms = extrair_dados_arquivo(caminho_arquivo)

                        if not data or not rms:
                            print("⚠️ Sem data ou RMS")
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
                            print("❌ RMS inválido")
                            continue

                        registro = {
                            "usina": os.path.basename(BASE_PATH),
                            "sala": sala,
                            "sub_sala": subsala,
                            "motor": motor,
                            "configuracao": config,
                            "arquivo": arquivo,
                            "data_arquivo": data_float,
                            "data_convertida": data_convertida,
                            "rms": rms_val,
                            "nivel1": nivel1,
                            "nivel2": nivel2
                        }

                        print(f"💾 Preparado: {registro}")

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

print("\n💾 Salvando no banco...")

for d in dados:
    try:
        Medicao.objects.create(
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
        )

        print("✅ Salvo no banco")

    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

print("🏁 FINALIZADO")