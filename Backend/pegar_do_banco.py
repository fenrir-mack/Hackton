import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from manutencao.models import Motor, Medicao

# =========================
# CONFIGURAÇÃO MANUAL
# =========================
motor_id = 199

# 👉 DATA do ponto extra (formato: dd/mm/aaaa)
data_limite_str = "27/08/2023"

# 👉 qual limite usar: "nivel1" ou "nivel2"
usar_nivel = "nivel2"
# =========================


motor = Motor.objects.get(id=motor_id)

medicoes = (
    Medicao.objects
    .filter(motor=motor)
    .order_by('data_convertida')
)

dados = []

for m in medicoes:
    dados.append({
        "data": m.data_convertida.strftime("%d/%m/%Y"),
        "rms": m.rms,
    })

# =========================
# ADICIONANDO PONTO FINAL
# =========================
data_limite = datetime.strptime(data_limite_str, "%d/%m/%Y")

if usar_nivel == "nivel1":
    valor_limite = motor.nivel1
else:
    valor_limite = motor.nivel2

dados.append({
    "data": data_limite.strftime("%d/%m/%Y"),
    "rms": valor_limite,
    "tipo": "limite"  # opcional (pra diferenciar no gráfico)
})
# =========================


resultado = {
    "motor": {
        "id": motor.id,
        "nome": motor.nome,
        "usina": motor.sala,
        "nivel1": motor.nivel1,
        "nivel2": motor.nivel2,
    },
    "medicoes": dados
}

print(json.dumps(resultado, indent=4, ensure_ascii=False))