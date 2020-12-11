from rest_framework import serializers

# Need a "sub-serializer" to handle self refernce MPTT tree structures
class RecursiveFieldSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data
