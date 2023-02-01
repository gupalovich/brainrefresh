from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from ..models import Question, Tag
from .serializers import QuestionDetailSerializer, QuestionListSerializer, TagSerializer


class TagViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = "slug"
    permission_classes = ()


class QuestionViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    CreateModelMixin,
    GenericViewSet,
):
    serializer_class = QuestionListSerializer
    lookup_field = "uuid"
    permission_classes = ()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuestionDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "retrieve":
            return Question.objects.prefetch_related("tags", "choices").published()
        return Question.objects.prefetch_related("tags").published()