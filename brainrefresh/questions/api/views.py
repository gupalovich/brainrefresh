from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiParameter
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import (
    AllowAny,
    IsAdminUser,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.viewsets import GenericViewSet

from .pagination import LimitOffsetPagination
from .serializers import (
    Answer,
    AnswerSerializer,
    Choice,
    ChoiceSerializer,
    Question,
    QuestionDetailSerializer,
    QuestionListSerializer,
    Tag,
    TagSerializer,
)
from .validators import compare_users_and_restrict


class TagViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Tag.objects.prefetch_related("questions")
    serializer_class = TagSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class QuestionViewSet(
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    class QuestionFilter(filters.FilterSet):
        user = filters.CharFilter(field_name="user__username", lookup_expr="exact")
        tag = filters.CharFilter(
            field_name="tags__slug", lookup_expr="icontains"
        )  # could change to ModelMultipleChoiceFilter if needed

        class Meta:
            model = Question
            fields = ["tag", "user", "language"]

    lookup_field = "uuid"
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = QuestionFilter
    pagination_class = LimitOffsetPagination
    parameters = [
        OpenApiParameter(
            name="language",
            type=str,
            description="Filter by language (EN or RU)",
            required=False,
        ),
    ]

    def get_serializer_class(self):
        if self.action in ["retrieve", "update"]:
            return QuestionDetailSerializer
        return QuestionListSerializer

    def get_queryset(self):
        query = Question.objects.select_related("user").prefetch_related("tags")
        if self.action in ["retrieve", "update"]:
            query = query.prefetch_related("choices")
        return query.published()

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        compare_users_and_restrict(self.request.user, instance.user, call_from="view")
        instance.delete()


class ChoiceViewSet(
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    lookup_field = "uuid"
    serializer_class = ChoiceSerializer
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == "list":
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = Choice.objects.select_related("question")
        return queryset

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(settings.API_CACHE_TIME))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        compare_users_and_restrict(
            self.request.user, instance.question.user, call_from="view"
        )
        instance.delete()


class AnswerViewSet(
    ListModelMixin,
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = AnswerSerializer
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = (
            Answer.objects.filter(user=self.request.user)
            .select_related("question")
            .prefetch_related("choices__question")
        )
        return queryset
