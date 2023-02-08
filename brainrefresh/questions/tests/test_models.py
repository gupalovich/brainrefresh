from uuid import UUID

from django.test import TestCase
from django.utils import timezone
from django.utils.text import slugify

from brainrefresh.users.tests.factories import UserFactory

from .factories import Choice, ChoiceFactory, Question, QuestionFactory, Tag, TagFactory


class TagTests(TestCase):
    def setUp(self):
        self.tag_data = {"label": "test tag"}
        self.tag_slug = slugify(self.tag_data["label"])
        self.tag = TagFactory(label=self.tag_data["label"])

    def test_create(self):
        tag = TagFactory(**self.tag_data)
        self.assertEqual(tag.label, self.tag_data["label"])

    def test_read(self):
        tag = TagFactory(**self.tag_data)
        read_tag = Tag.objects.get(id=tag.id)
        self.assertEqual(read_tag.label, self.tag_data["label"])

    def test_update(self):
        new_label = "Updated Test Tag"
        tag = TagFactory(**self.tag_data)
        tag.label = new_label
        tag.save()
        updated_tag = Tag.objects.get(id=tag.id)
        self.assertEqual(updated_tag.label, new_label)

    def test_delete(self):
        tag = TagFactory(**self.tag_data)
        tag.delete()
        with self.assertRaises(Tag.DoesNotExist):
            Tag.objects.get(id=tag.id)

    def test_str(self):
        self.assertEqual(str(self.tag), self.tag_data["label"])

    def test_slug_generation(self):
        self.assertTrue(self.tag.slug)

    def test_slug_uniqueness(self):
        new_tag = TagFactory(label=self.tag_data["label"])
        self.assertNotEqual(self.tag.slug, new_tag.slug)
        self.assertTrue(f"{self.tag_slug}-1" in new_tag.slug)

    def test_label_change_updates_slug(self):
        previous_slug = self.tag.slug
        self.tag.label = "updated label"
        self.tag.save()
        self.assertNotEqual(previous_slug, self.tag.slug)

    def test_label_change_doesnt_update_slug_if_unmodified(self):
        previous_slug = self.tag.slug
        self.tag.save()
        self.assertEqual(previous_slug, self.tag.slug)


class QuestionTests(TestCase):
    def setUp(self):
        self.user = UserFactory(username="testuser", password="12345")
        self.tag = TagFactory(label="test_tag")
        self.question_data = {
            "user": self.user,
            "title": "Test Question Title",
            "text": "Test Question Text",
            "explanation": "Test explanation",
            "language": Question.Lang.EN,
            "published": True,
        }
        self.question = QuestionFactory(**self.question_data)

    def test_create(self):
        self.assertEqual(Question.objects.count(), 1)

    def test_update(self):
        new_title = "Updated test question"
        self.question.title = new_title
        self.question.save()
        self.question.refresh_from_db()
        self.assertEqual(Question.objects.count(), 1)
        self.assertEqual(self.question.title, new_title)

    def test_delete(self):
        self.question.delete()
        self.assertEqual(Question.objects.count(), 0)

    def test_str(self):
        self.assertEqual(str(self.question), self.question_data["title"])

    def test_fields(self):
        self.assertEqual(self.question.title, self.question_data["title"])
        self.assertEqual(self.question.text, self.question_data["text"])
        self.assertEqual(self.question.language, Question.Lang.EN)
        self.assertEqual(self.question.published, True)
        self.assertIsInstance(self.question.uuid, UUID)
        self.assertIsInstance(self.question.created_at, timezone.datetime)
        self.assertIsInstance(self.question.updated_at, timezone.datetime)

    def test_related_fields(self):
        self.question.tags.add(self.tag)
        self.question.refresh_from_db()
        # tests
        self.assertEqual(self.question.user, self.user)
        self.assertIn(self.tag, self.question.tags.all())


class ChoiceTests(TestCase):
    def setUp(self):
        self.question_data = {
            "title": "Test Question Title",
            "text": "Test Question Text",
            "explanation": "Test explanation",
            "language": Question.Lang.EN,
            "published": True,
        }
        self.question = QuestionFactory(**self.question_data)
        self.choice_data = {
            "question": self.question,
            "text": "Test Choice",
            "is_correct": False,
        }
        self.choice = ChoiceFactory(**self.choice_data)
        ChoiceFactory.create_batch(5, question=self.question)

    def test_create(self):
        self.assertEqual(Choice.objects.count(), 6)

    def test_update(self):
        new_text = "Updated test question"
        self.choice.text = new_text
        self.choice.save()
        self.choice.refresh_from_db()
        self.assertEqual(self.choice.text, new_text)

    def test_delete(self):
        self.choice.delete()
        self.assertEqual(Choice.objects.count(), 5)

    def test_fields(self):
        self.assertIsInstance(self.choice, Choice)
        self.assertIsInstance(self.choice.uuid, UUID)
        self.assertEqual(self.choice.text, self.choice_data["text"])
        self.assertFalse(self.choice.is_correct)

    def test_str(self):
        self.assertEqual(
            str(self.choice), f"{self.question.title} : {str(self.choice.uuid)}"
        )

    def test_related_fields(self):
        self.assertIsInstance(self.choice.question, Question)
        self.assertEqual(self.choice.question, self.question)

    def test_delete_cascade(self):
        choice_id = self.choice.id
        self.question.delete()
        with self.assertRaises(Choice.DoesNotExist):
            Choice.objects.get(id=choice_id)
