from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "file", "status", "error_message", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "error_message", "created_at", "updated_at"]

    def validate_file(self, value):
        if not value.name.lower().endswith((".txt", ".md", ".pdf")):
            raise serializers.ValidationError("Upload a .txt, .md, or .pdf file.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be 10 MB or less.")
        return value


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=4000)
    document_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=False
    )
    top_k = serializers.IntegerField(min_value=1, max_value=10, default=5)
