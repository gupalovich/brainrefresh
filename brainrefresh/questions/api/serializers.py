from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ..models import Answer, Choice, Question, Tag
from .validators import compare_users_and_restrict, validate_two_uuids


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["url", "label", "slug", "question_count"]
        extra_kwargs = {"url": {"view_name": "api:tag-detail", "lookup_field": "slug"}}


class QuestionBaseSerializer(serializers.ModelSerializer):
    class TagsSerializer(serializers.Serializer):
        url = serializers.HyperlinkedIdentityField(
            view_name="api:tag-detail", lookup_field="slug"
        )
        label = serializers.CharField(read_only=True)
        slug = serializers.SlugField()

    class CreatorSerializer(serializers.Serializer):
        username = serializers.CharField()
        name = serializers.CharField()

    class Meta:
        model = Question
        fields = [
            "url",
            "uuid",
            "user",
            "title",
            "text",
            "explanation",
            "language",
            "is_multichoice",
            "updated_at",
            "created_at",
            "tags",
        ]

    url = serializers.HyperlinkedIdentityField(
        view_name="api:question-detail", lookup_field="uuid"
    )
    creator = CreatorSerializer(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = TagsSerializer(Tag.objects.all(), many=True, required=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["creator"] = self.CreatorSerializer(instance.user).data
        return representation


class QuestionListSerializer(QuestionBaseSerializer):
    class Meta:
        model = QuestionBaseSerializer.Meta.model
        fields = QuestionBaseSerializer.Meta.fields
        extra_kwargs = {
            "text": {"write_only": True},
            "explanation": {"write_only": True},
        }

    def create(self, validated_data):
        # pop tags
        tags_data = validated_data.pop("tags", [])
        tag_slugs = [tag["slug"] for tag in tags_data if "slug" in tag]
        # create question, filter tags by slugs
        question = Question.objects.create(**validated_data)
        tags = Tag.objects.filter(slug__in=tag_slugs)
        # set tags if any
        question.tags.set(tags)
        return question


class QuestionDetailChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = [
            "url",
            "uuid",
            "text",
            "is_correct",
        ]
        extra_kwargs = {
            "is_correct": {"write_only": True},
        }

    url = serializers.HyperlinkedIdentityField(
        view_name="api:choice-detail", lookup_field="uuid"
    )


class QuestionDetailSerializer(QuestionBaseSerializer):
    class Meta:
        model = QuestionBaseSerializer.Meta.model
        fields = QuestionBaseSerializer.Meta.fields + [
            "choices",
        ]

    choices = QuestionDetailChoicesSerializer(many=True, read_only=True)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        # validate users
        compare_users_and_restrict(request.user, instance.user)
        # pop tags
        tags_data = validated_data.pop("tags", [])
        tag_slugs = [tag["slug"] for tag in tags_data if "slug" in tag]
        # update question, filter tags by slugs
        question = super().update(instance, validated_data)
        tags = Tag.objects.filter(slug__in=tag_slugs)
        # set tags if any
        question.tags.set(tags)
        return question


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["url", "uuid", "question", "question_url", "text", "is_correct"]

    url = serializers.HyperlinkedIdentityField(
        view_name="api:choice-detail", lookup_field="uuid"
    )
    question_url = serializers.SerializerMethodField()
    question = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Question.objects.all()
    )

    @extend_schema_field(OpenApiTypes.URI)
    def get_question_url(self, obj):
        request = self.context.get("request")
        rev = reverse("api:question-detail", kwargs={"uuid": obj.question.uuid})
        return request.build_absolute_uri(rev)

    def create(self, validated_data):
        request = self.context.get("request")
        question = validated_data.get("question")
        # validate users
        compare_users_and_restrict(request.user, question.user)
        # create call
        choice = Choice.objects.create(**validated_data)
        return choice

    def update(self, instance, validated_data):
        request = self.context.get("request")
        question = validated_data.get("question")
        # validate users
        compare_users_and_restrict(request.user, question.user)
        # update call
        choice = super().update(instance, validated_data)
        return choice


class AnswerSerializer(serializers.ModelSerializer):
    class ChoicesSerializer(serializers.Serializer):
        uuid = serializers.UUIDField()
        text = serializers.CharField(read_only=True)
        is_correct = serializers.BooleanField(read_only=True)

    class Meta:
        model = Answer
        fields = [
            "url",
            "uuid",
            "user",
            "question",
            "choices",
            "is_correct",
            "created_at",
        ]
        extra_kwargs = {
            "url": {"view_name": "api:answer-detail", "lookup_field": "uuid"},
        }

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    question = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Question.objects.all()
    )
    choices = ChoicesSerializer(many=True)

    @transaction.atomic()
    def create(self, validated_data):
        question = validated_data.pop("question")
        choices_data = validated_data.pop("choices")
        # create answer
        answer = Answer.objects.create(question=question, **validated_data)
        # loop over nested choices and validate question uuids
        for choice_data in choices_data:
            choice = get_object_or_404(Choice, uuid=choice_data["uuid"])
            validate_two_uuids(question.uuid, choice.question.uuid)
            answer.choices.add(choice)
        return answer
