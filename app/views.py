from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from account.models import User
from account.serializers import UserSerializer
from django.contrib.auth import get_user_model
from rest_framework import filters
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from app.serializers import (SearchUserSerializers, FriendshipRequestSerializer, ShowFriendRequestSerializer,
                             ShowFriendListSerializer,
                             )
from app.models import FriendshipRequest
import json
from django.core.serializers import serialize
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()




class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class SearchUserView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'email']

    def get_queryset(self):
        query = self.request.query_params.get('query', None)

        
        if query:
            if "@" in query or "." in query:
                users = User.objects.filter(email=query.lower())
                return users

            search_terms = query.lower().split()
            q_objects = Q()
            for term in search_terms:
                q_objects |= Q(first_name__icontains=term) | Q(last_name__icontains=term)
            return User.objects.filter(q_objects)
        return User.objects.none()
    
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginator = CustomPagination()
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = SearchUserSerializers(result_page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)







class SendFriendRequestView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    queryset = FriendshipRequest.objects.all()
    serializer_class = FriendshipRequestSerializer
    def get(self, request, *args, **kwargs):
        sender = request.user
        receiver_id = kwargs.get("receiver_id")
        try:
            receiver = User.objects.get(id=receiver_id)
            if FriendshipRequest.objects.filter(sender=sender, receiver=receiver).exists():
                return Response({"error": "Friendship request already sent."}, status=status.HTTP_400_BAD_REQUEST)
            
            if FriendshipRequest.objects.filter(receiver=sender, sender=receiver).exists():

                is_friend = FriendshipRequest.objects.filter(receiver=sender, sender=receiver).first()
                if is_friend.status == "accepted":
                    return Response({"message": "Already friend."}, status=status.HTTP_200_OK)

                return Response({"message": "other person sent you request already please check your request section and accept it"}, status=status.HTTP_400_BAD_REQUEST)

            one_minute_ago = timezone.now() - timedelta(minutes=1)
            request_count = FriendshipRequest.objects.filter(sender=sender, created_at__gte=one_minute_ago).count()
            if request_count >= 3:
                
                return Response({"error": "You can only send 3 requests per minute."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            FriendshipRequest.objects.create(sender=sender, receiver=receiver)
            return Response({"message": "Friendship request sent successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "Receiver user does not exist."}, status=status.HTTP_404_NOT_FOUND)





class FriendRequestView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):

        pending_requests = FriendshipRequest.objects.filter(receiver=request.user, status="pending")
        serializer = ShowFriendRequestSerializer(pending_requests, many=True)
        return Response({"friend_requests": serializer.data}, status=status.HTTP_200_OK)
    


class AcceptFriendRequestView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
       
        
        
        user = User.objects.get(id=user_id)

  
        is_request = FriendshipRequest.objects.filter(sender=user, receiver=request.user).exists()
   
        if is_request:
            is_request = is_request = FriendshipRequest.objects.filter(sender=user, receiver=request.user).first()
     
            is_request.status="accepted"
            is_request.save()
     
            return Response("Request Accepted", status=status.HTTP_200_OK)
        return Response("some thing went wrong : ", status=status.HTTP_400_BAD_REQUEST)






class RejectFriendRequestView(GenericAPIView):
    parser_classes = [IsAuthenticated]
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        try:
            user = User.objects.get(id=user_id)
            is_request = FriendshipRequest.objects.filter(sender=user, receiver=request.user).exists()
            
            if is_request:
                is_request = is_request = FriendshipRequest.objects.filter(sender=user, receiver=request.user).first()
        
                is_request.status="rejected"
                is_request.save()
        
                return Response("Request Rejected", status=status.HTTP_200_OK)
        except Exception as e:
            return Response("Either user does not exists or got error : ", status=status.HTTP_400_BAD_REQUEST)





class GetMyAllFriendView(GenericAPIView):
    queryset = FriendshipRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    
    def get(self, request, *args, **kwargs):
        user = request.user 
        friends = FriendshipRequest.objects.filter(
            Q(sender=user) | Q(receiver=user),
            status="accepted"
            ).select_related('sender', 'receiver')
        if not friends:
            return Response({"my_friends":[]}, status=status.HTTP_200_OK)
        my_friends = []
        for friend in friends:
            if friend.sender == user:
                unique_id = friend.receiver.id
                first_name = friend.receiver.first_name
                last_name = friend.receiver.last_name
                email =  friend.receiver.email
            else:
                first_name = friend.sender.first_name
                last_name = friend.sender.last_name
                email =  friend.sender.email
                unique_id = friend.sender.id


            
            result = {
                "unique_id":unique_id ,
                "email" : email,
                "first_name":first_name,
                "last_name" : last_name,          
            }
            my_friends.append(result)

        return Response({"my_friends":my_friends}, status=status.HTTP_200_OK)
    








