from django.urls import path 
from app.views import (SearchUserView, SendFriendRequestView, FriendRequestView, 
                       AcceptFriendRequestView, RejectFriendRequestView, GetMyAllFriendView ,
                       )
urlpatterns = [
        path("search/",SearchUserView.as_view(), name="search-user"),
        path("send-friend-req/<str:receiver_id>/",SendFriendRequestView.as_view(), name="send-friend-req"),# send frd req
        path("view-friend-req/",FriendRequestView.as_view(), name = "accept-req-and-view"),
        path("accept-req/<str:user_id>/",AcceptFriendRequestView.as_view(), name="accept-req"),
        path("reject-req/<str:user_id>/",RejectFriendRequestView.as_view(), name="reject-req"),
        path("friends/",GetMyAllFriendView.as_view(), name="friends" ),
       


        
]