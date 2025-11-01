from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Follow, User
from .models import PrayerInteraction, PrayerNotification, PrayerRequest


class PrayerRequestAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="requester",
            email="requester@example.com",
            password="password123",
        )
        self.friend = User.objects.create_user(
            username="friend",
            email="friend@example.com",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
        )
        self.list_url = reverse("prayerrequest-list")

    def test_create_prayer_request(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "short_description": "Please pray for our outreach weekend.",
            "visibility": "public",
            "category": "Community",
        }
        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PrayerRequest.objects.count(), 1)
        prayer = PrayerRequest.objects.first()
        self.assertEqual(prayer.user, self.user)
        self.assertEqual(prayer.short_description, payload["short_description"])

    def test_anonymous_request_hides_user_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.list_url,
            {"short_description": "Anonymous prayer", "visibility": "anonymous"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 1)
        self.assertIsNone(data[0]["user_profile"])

    def test_friend_visibility(self):
        Follow.objects.create(follower=self.friend, following=self.user)
        self.client.force_authenticate(user=self.user)
        self.client.post(
            self.list_url,
            {
                "short_description": "Pray for exams",
                "visibility": "friends",
            },
            format="json",
        )

        self.client.force_authenticate(user=self.friend)
        response = self.client.get(self.list_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get("results", [])
        self.assertEqual(len(data), 1)

    def test_pray_action_records_prayer(self):
        self.client.force_authenticate(user=self.user)
        create_response = self.client.post(
            self.list_url,
            {"short_description": "Pray for healing"},
            format="json",
        )
        prayer_id = create_response.data["id"]
        pray_url = reverse("prayerrequest-pray", args=[prayer_id])

        self.client.force_authenticate(user=self.friend)
        response = self.client.post(pray_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            PrayerInteraction.objects.filter(
                prayer_request_id=prayer_id,
                interaction_type=PrayerInteraction.InteractionType.PRAYED,
            ).count(),
            1,
        )

    def test_mark_answered_sends_notifications(self):
        self.client.force_authenticate(user=self.user)
        create_response = self.client.post(
            self.list_url,
            {"short_description": "Pray for a job"},
            format="json",
        )
        prayer_id = create_response.data["id"]

        pray_url = reverse("prayerrequest-pray", args=[prayer_id])
        self.client.force_authenticate(user=self.friend)
        self.client.post(pray_url, format="json")

        mark_answered_url = reverse("prayerrequest-mark-answered", args=[prayer_id])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            mark_answered_url,
            {"answered_note": "God provided in full!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prayer = PrayerRequest.objects.get(pk=prayer_id)
        self.assertEqual(prayer.status, PrayerRequest.Status.ANSWERED)
        self.assertEqual(
            PrayerNotification.objects.filter(
                prayer_request_id=prayer_id,
                notification_type=PrayerNotification.NotificationType.ANSWERED,
            ).count(),
            1,
        )
