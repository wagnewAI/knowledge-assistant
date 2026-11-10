from pathlib import Path

from django.db import transaction
from pypdf import PdfReader
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Chunk, Document
from .serializers import AskSerializer, DocumentSerializer
from .services import answer_question, embed_texts, split_text


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        document = serializer.save(owner=self.request.user)
        try:
            path = Path(document.file.path)
            if path.suffix.lower() == ".pdf":
                raw_text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
            else:
                raw_text = path.read_text(encoding="utf-8", errors="replace")
            texts = split_text(raw_text)
            if not texts:
                raise ValueError("No readable text was found in the file.")
            vectors = embed_texts(texts)
            with transaction.atomic():
                Chunk.objects.bulk_create([
                    Chunk(document=document, ordinal=index, text=chunk_text, embedding=vector)
                    for index, (chunk_text, vector) in enumerate(zip(texts, vectors), start=1)
                ])
                document.status = Document.Status.READY
                document.error_message = ""
                document.save(update_fields=["status", "error_message", "updated_at"])
        except Exception as exc:
            document.status = Document.Status.FAILED
            document.error_message = str(exc)[:500]
            document.save(update_fields=["status", "error_message", "updated_at"])

    @action(detail=True, methods=["post"])
    def reindex(self, request, pk=None):
        document = self.get_object()
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])
        Chunk.objects.filter(document=document).delete()
        try:
            path = Path(document.file.path)
            if path.suffix.lower() == ".pdf":
                raw_text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
            else:
                raw_text = path.read_text(encoding="utf-8", errors="replace")
            texts = split_text(raw_text)
            if not texts:
                raise ValueError("No readable text was found in the file.")
            vectors = embed_texts(texts)
            Chunk.objects.bulk_create([
                Chunk(document=document, ordinal=i, text=t, embedding=v)
                for i, (t, v) in enumerate(zip(texts, vectors), start=1)
            ])
            document.status = Document.Status.READY
            document.error_message = ""
        except Exception as exc:
            document.status = Document.Status.FAILED
            document.error_message = str(exc)[:500]
        document.save(update_fields=["status", "error_message", "updated_at"])
        return Response(DocumentSerializer(document).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ask(request):
    serializer = AskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    document_ids = data.get("document_ids")
    if document_ids is not None:
        owned_ids = set(Document.objects.filter(owner=request.user, id__in=document_ids).values_list("id", flat=True))
        if owned_ids != set(document_ids):
            raise ValidationError({"document_ids": "One or more documents are unavailable."})
    try:
        result = answer_question(request.user, data["question"], data["top_k"], document_ids)
    except Exception as exc:
        raise APIException(str(exc)) from exc
    return Response(result, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def health(request):
    return Response({"status": "ok"})
