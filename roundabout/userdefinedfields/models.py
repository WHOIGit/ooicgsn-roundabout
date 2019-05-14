from django.db import models



# Create your models here.

class Field(models.Model):
    FIELD_TYPES = (
        ('CharField', 'Text Field'),
        ('IntegerField', 'Integer Field'),
        ('DecimalField', 'Decimal Field'),
        ('DateField', 'Date Field'),
        ('BooleanField', 'Boolean Field'),
    )
    field_name = models.CharField(max_length=255, unique=True, db_index=True)
    field_description = models.CharField(max_length=255, null=False, blank=True)
    field_type = models.CharField(max_length=100, choices=FIELD_TYPES)
    field_default_value = models.CharField(max_length=255, null=False, blank=True)
    global_for_part_types = models.ManyToManyField('parts.PartType', blank=True)

    class Meta:
        ordering = ('field_name',)

    def __str__(self):
        return self.field_name
