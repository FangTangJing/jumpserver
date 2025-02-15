from rest_framework.mixins import ListModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.views import APIView
from rest_framework.response import Response

from common.drf.api import JMSGenericViewSet
from common.permissions import IsObjectOwner, IsSuperUser, OnlySuperUserCanList
from notifications.notifications import system_msgs
from notifications.models import SystemMsgSubscription, UserMsgSubscription
from notifications.backends import BACKEND
from notifications.serializers import (
    SystemMsgSubscriptionSerializer, SystemMsgSubscriptionByCategorySerializer,
    UserMsgSubscriptionSerializer,
)

__all__ = ('BackendListView', 'SystemMsgSubscriptionViewSet', 'UserMsgSubscriptionViewSet')


class BackendListView(APIView):
    def get(self, request):
        data = [
            {
                'name': backend,
                'name_display': backend.label
            }
            for backend in BACKEND
            if backend.is_enable
        ]
        return Response(data=data)


class SystemMsgSubscriptionViewSet(ListModelMixin,
                                   UpdateModelMixin,
                                   JMSGenericViewSet):
    lookup_field = 'message_type'
    queryset = SystemMsgSubscription.objects.all()
    serializer_classes = {
        'list': SystemMsgSubscriptionByCategorySerializer,
        'update': SystemMsgSubscriptionSerializer,
        'partial_update': SystemMsgSubscriptionSerializer
    }

    def list(self, request, *args, **kwargs):
        data = []
        category_children_mapper = {}

        subscriptions = self.get_queryset()
        msgtype_sub_mapper = {}
        for sub in subscriptions:
            msgtype_sub_mapper[sub.message_type] = sub

        for msg in system_msgs:
            message_type = msg['message_type']
            message_type_label = msg['message_type_label']
            category = msg['category']
            category_label = msg['category_label']

            if category not in category_children_mapper:
                children = []

                data.append({
                    'category': category,
                    'category_label': category_label,
                    'children': children
                })
                category_children_mapper[category] = children

            sub = msgtype_sub_mapper[message_type]
            sub.message_type_label = message_type_label
            category_children_mapper[category].append(sub)

        serializer = self.get_serializer(data, many=True)
        return Response(data=serializer.data)


class UserMsgSubscriptionViewSet(ListModelMixin,
                                 RetrieveModelMixin,
                                 UpdateModelMixin,
                                 JMSGenericViewSet):
    lookup_field = 'user_id'
    queryset = UserMsgSubscription.objects.all()
    serializer_class = UserMsgSubscriptionSerializer
    permission_classes = (IsObjectOwner | IsSuperUser, OnlySuperUserCanList)
