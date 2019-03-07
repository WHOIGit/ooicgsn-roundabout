from django.db import models

# Create your models here.

class Printer(models.Model):
    PRINTER_TYPES = (
        ('Brady', 'Brady'),
        ('Zebra', 'Zebra'),
    )
    name = models.CharField(max_length=255, unique=False, db_index=True)
    ip_domain = models.CharField(max_length=255, unique=True)
    printer_type = models.CharField(max_length=20, choices=PRINTER_TYPES, default='Brady')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
