from django.db import models
from django.db.models import Count, Exists, OuterRef, Prefetch
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import Follow

from .models import PrayerInteraction, PrayerNotification, PrayerRequest
from .serializers import PrayerEncouragementSerializer, PrayerRequestSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user_id == getattr(request.user, "id", None)


class PrayerRequestViewSet(viewsets.ModelViewSet):
    queryset = PrayerRequest.objects.all()
    serializer_class = PrayerRequestSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        queryset = (
            PrayerRequest.objects.select_related("user")
            .annotate(
                prayer_count=Count(
                    "interactions",
                    filter=models.Q(
                        interactions__interaction_type=PrayerInteraction.InteractionType.PRAYED
                    ),
                    distinct=True,
                ),
                encouragement_count=Count(
                    "interactions",
                    filter=models.Q(
                        interactions__interaction_type=PrayerInteraction.InteractionType.ENCOURAGE
                    ),
                    distinct=True,
                ),
            )
            .prefetch_related(
                Prefetch(
                    "interactions",
                    queryset=PrayerInteraction.objects.filter(
                        interaction_type=PrayerInteraction.InteractionType.ENCOURAGE
                    )
                    .select_related("user")
                    .order_by("-created_at")[:5],
                    to_attr="_recent_encouragements",
                )
            )
        )

        if user.is_authenticated:
            queryset = queryset.annotate(
                has_prayed=Exists(
                    PrayerInteraction.objects.filter(
                        prayer_request=OuterRef("pk"),
                        user=user,
                        interaction_type=PrayerInteraction.InteractionType.PRAYED,
                    )
                )
            )

            following_ids = Follow.objects.filter(follower=user).values_list(
                "following_id", flat=True
            )
            visibility_filter = (
                models.Q(visibility=PrayerRequest.Visibility.PUBLIC)
                | models.Q(visibility=PrayerRequest.Visibility.ANONYMOUS)
                | models.Q(user=user)
                | models.Q(
                    visibility=PrayerRequest.Visibility.FRIENDS,
                    user_id__in=following_ids,
                )
            )
            queryset = queryset.filter(visibility_filter)
        else:
            queryset = queryset.filter(
                models.Q(visibility=PrayerRequest.Visibility.PUBLIC)
                | models.Q(visibility=PrayerRequest.Visibility.ANONYMOUS)
            )

        status_filter = self.request.query_params.get("status")
        if status_filter in dict(PrayerRequest.Status.choices):
            queryset = queryset.filter(status=status_filter)

        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__iexact=category.strip())

        sort = self.request.query_params.get("sort", "newest").lower()
        if sort == "most_prayed":
            queryset = queryset.order_by("-prayer_count", "-created_at")
        elif sort == "answered":
            queryset = queryset.filter(status=PrayerRequest.Status.ANSWERED).order_by(
                "-answered_at", "-created_at"
            )
        else:
            queryset = queryset.order_by("-created_at")

        return queryset

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action in ["create", "pray", "unpray", "mark_answered"]:
            self.permission_classes = [permissions.IsAuthenticated]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"], url_path="pray")
    def pray(self, request, pk=None):
        prayer_request = self.get_object()

        interaction, created = PrayerInteraction.objects.get_or_create(
            prayer_request=prayer_request,
            user=request.user,
            interaction_type=PrayerInteraction.InteractionType.PRAYED,
        )

        if not created:
            return Response(
                {
                    "detail": "You have already recorded a prayer for this request.",
                    "prayer_count": PrayerInteraction.objects.filter(
                        prayer_request=prayer_request,
                        interaction_type=PrayerInteraction.InteractionType.PRAYED,
                    ).count(),
                },
                status=status.HTTP_200_OK,
            )

        if prayer_request.user and prayer_request.user != request.user:
            PrayerNotification.objects.get_or_create(
                recipient=prayer_request.user,
                actor=request.user,
                prayer_request=prayer_request,
                notification_type=PrayerNotification.NotificationType.PRAYED,
                defaults={
                    "payload": {
                        "prayer_request_id": str(prayer_request.id),
                        "prayer_request": prayer_request.short_description,
                    }
                },
            )

        prayer_count = PrayerInteraction.objects.filter(
            prayer_request=prayer_request,
            interaction_type=PrayerInteraction.InteractionType.PRAYED,
        ).count()

        return Response(
            {"detail": "Prayer recorded.", "prayer_count": prayer_count},
            status=status.HTTP_200_OK,
        )

    @pray.mapping.delete
    def unpray(self, request, pk=None):
        prayer_request = self.get_object()

        deleted, _ = PrayerInteraction.objects.filter(
            prayer_request=prayer_request,
            user=request.user,
            interaction_type=PrayerInteraction.InteractionType.PRAYED,
        ).delete()

        if not deleted:
            return Response(
                {"detail": "Prayer record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        prayer_count = PrayerInteraction.objects.filter(
            prayer_request=prayer_request,
            interaction_type=PrayerInteraction.InteractionType.PRAYED,
        ).count()

        return Response(
            {"detail": "Prayer removed.", "prayer_count": prayer_count},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"], url_path="encouragements")
    def encouragements(self, request, pk=None):
        prayer_request = self.get_object()

        if request.method.lower() == "post":
            if not request.user.is_authenticated:
                return Response(
                    {"detail": "Authentication required to encourage."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            message = (request.data.get("message") or "").strip()
            if not message:
                return Response(
                    {"detail": "Encouragement message cannot be empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if len(message) > 100:
                return Response(
                    {"detail": "Encouragement must be 100 characters or fewer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            encouragement = PrayerInteraction.objects.create(
                prayer_request=prayer_request,
                user=request.user,
                interaction_type=PrayerInteraction.InteractionType.ENCOURAGE,
                message=message,
            )

            serializer = PrayerEncouragementSerializer(encouragement)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        queryset = PrayerInteraction.objects.filter(
            prayer_request=prayer_request,
            interaction_type=PrayerInteraction.InteractionType.ENCOURAGE,
        ).select_related("user")
        serializer = PrayerEncouragementSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="mark-answered")
    def mark_answered(self, request, pk=None):
        prayer_request = self.get_object()

        if prayer_request.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        answered_note = (request.data.get("answered_note") or "").strip()
        answered_scripture = (request.data.get("answered_scripture") or "").strip()

        if len(answered_note) > 200:
            return Response(
                {"detail": "Thank-you note must be 200 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(answered_scripture) > 120:
            return Response(
                {"detail": "Scripture reference must be 120 characters or fewer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        prayer_request.status = PrayerRequest.Status.ANSWERED
        prayer_request.answered_note = answered_note
        prayer_request.answered_scripture = answered_scripture
        prayer_request.answered_at = timezone.now()
        prayer_request.save(update_fields=[
            "status",
            "answered_note",
            "answered_scripture",
            "answered_at",
            "updated_at",
        ])

        prayed_user_ids = (
            PrayerInteraction.objects.filter(
                prayer_request=prayer_request,
                interaction_type=PrayerInteraction.InteractionType.PRAYED,
            )
            .exclude(user=request.user)
            .values_list("user_id", flat=True)
            .distinct()
        )

        notifications = []
        for recipient_id in prayed_user_ids:
            notifications.append(
                PrayerNotification(
                    recipient_id=recipient_id,
                    actor=request.user,
                    prayer_request=prayer_request,
                    notification_type=PrayerNotification.NotificationType.ANSWERED,
                    payload={
                        "prayer_request_id": str(prayer_request.id),
                        "prayer_request": prayer_request.short_description,
                        "thank_you": answered_note,
                    },
                )
            )
        if notifications:
            PrayerNotification.objects.bulk_create(notifications, ignore_conflicts=True)

        serializer = self.get_serializer(prayer_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="prayed-users")
    def prayed_users(self, request, pk=None):
        prayer_request = self.get_object()

        interactions = (
            PrayerInteraction.objects.filter(
                prayer_request=prayer_request,
                interaction_type=PrayerInteraction.InteractionType.PRAYED,
            )
            .select_related("user")
            .order_by("-created_at")
        )

        data = [
            {
                "id": interaction.user_id,
                "username": interaction.user.username,
                "display_name": interaction.user.get_full_name() or interaction.user.username,
                "avatar": getattr(interaction.user, "profile_picture", None),
                "prayed_at": interaction.created_at,
            }
            for interaction in interactions
        ]

        return Response(data)

    @action(detail=False, methods=["get"], url_path="answered")
    def answered(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=PrayerRequest.Status.ANSWERED)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)