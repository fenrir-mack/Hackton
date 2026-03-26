from django.db import models


class Motor(models.Model):
    usina = models.CharField(max_length=255)
    sala = models.CharField(max_length=255)
    sub_sala = models.CharField(max_length=255, null=True, blank=True)
    nome = models.CharField(max_length=255)
    configuracao = models.CharField(max_length=255)

    # limites configurados do motor
    nivel1 = models.FloatField()
    nivel2 = models.FloatField()

    def __str__(self):
        return f"{self.usina} - {self.nome}"


class Medicao(models.Model):
    motor = models.ForeignKey(Motor,on_delete=models.CASCADE,related_name='medicoes',db_index=True)

    data_arquivo = models.DateTimeField()
    data_convertida = models.DateTimeField(db_index=True)

    rms = models.FloatField()

    class Meta:
        ordering = ['-data_convertida']  # mais recente primeiro
        indexes = [
            models.Index(fields=['motor', 'data_convertida']),
        ]

    def __str__(self):
        return f"{self.motor.nome} - {self.data_convertida}"


class ResultadoMotor(models.Model):
    motor = models.OneToOneField(Motor,on_delete=models.CASCADE,related_name='resultado')
    resultado_data_aviso = models.DateTimeField(null=True, blank=True)
    resultado_data_manutencao = models.DateTimeField(null=True, blank=True)

    manutencao_recente = models.BooleanField(default=False)
    ja_bateu_no_limite = models.BooleanField(default=False)

    def __str__(self):
        return f"Resultado - {self.motor.nome}"