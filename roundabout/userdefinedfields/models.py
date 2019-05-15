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


class FieldValue(models.Model):
    field_value = models.CharField(max_length=255, unique=False, db_index=True, null=False, blank=True)
    field = models.ForeignKey(Field, related_name='fieldvalues',
                          on_delete=models.CASCADE, null=False, blank=False)
    inventory = models.ForeignKey('inventory.Inventory', related_name='fieldvalues',
                          on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ('field', 'created_at')
        get_latest_by = 'created_at'

    def __str__(self):
        return self.field_value
