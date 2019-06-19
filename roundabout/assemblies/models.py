from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

from roundabout.locations.models import Location
from roundabout.parts.models import Part

# Assembly Types model
class AssemblyType(models.Model):
    name = models.CharField(max_length=255, unique=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

# Assembly base model
class Assembly(models.Model):
    name = models.CharField(max_length=255, unique=False, db_index=True)
    assembly_type = models.ForeignKey(AssemblyType, related_name='assemblies',
                                    on_delete=models.SET_NULL, null=True, blank=True)
    assembly_number = models.CharField(max_length=100, unique=False, db_index=True, null=False, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name


# Assembly documentation model
class AssemblyDocument(models.Model):
    DOC_TYPES = (
        ('Test', 'Test Documentation'),
        ('Design', 'Design Documentation'),
    )
    name = models.CharField(max_length=255, unique=False)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    doc_link = models.CharField(max_length=1000)
    assembly = models.ForeignKey(Assembly, related_name='assembly_documents',
                             on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['doc_type', 'name']

    def __str__(self):
        return self.name


# Assembly parts model
class AssemblyPart(MPTTModel):
    assembly = models.ForeignKey(Assembly, related_name='assembly_parts',
                          on_delete=models.CASCADE, null=False, blank=False, db_index=True)
    part = models.ForeignKey(Part, related_name='assembly_parts',
                          on_delete=models.CASCADE, null=False, blank=False, db_index=True)
    parent = TreeForeignKey('self', related_name='children',
                            on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    note = models.TextField(blank=True)
    order = models.CharField(max_length=255, null=False, blank=True, db_index=True)

    class MPTTMeta:
        order_insertion_by = ['order']

    def __str__(self):
        return self.part.name

    def get_assembly_total_cost(self):
        tree = self.get_descendants(include_self=True)
        total_cost = 0
        for item in tree:
            revision = item.part.revisions.first()
            cost = revision.unit_cost
            total_cost = total_cost + cost
        return total_cost

    def get_descendants_with_self(self):
        tree = self.get_descendants(include_self=True)
        return tree
