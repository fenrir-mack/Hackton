from django.db import models

class Medicao(models.Model):
    usina = models.CharField(max_length=255)
    sala = models.CharField(max_length=255)
    sub_sala = models.CharField(max_length=255, null=True, blank=True)  # 🔥 NOVO
    motor = models.CharField(max_length=255)

    configuracao = models.CharField(max_length=255)

    arquivo = models.CharField(max_length=255)

    data_arquivo = models.FloatField(null=True, blank=True)
    data_convertida = models.DateTimeField()

    rms = models.FloatField()

    nivel1 = models.FloatField()
    nivel2 = models.FloatField()