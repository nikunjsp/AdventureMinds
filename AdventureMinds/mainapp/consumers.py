import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from .models import UserChat, ChatMessage, ChatGroup, UserProfile

User = get_user_model()


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        user = self.scope['user']
        if user.is_authenticated:
            self.user = user
            chat_room = f'user_chatroom_{user.id}'
            self.chat_room = chat_room
            await self.channel_layer.group_add(
                chat_room,
                self.channel_name
            )
            await self.send({
                'type': 'websocket.accept'
            })

    async def websocket_receive(self, event):
        received_data = json.loads(event['text'])
        message = received_data.get('message')
        userchat_id = received_data.get('userchat_id')
        user_id = received_data.get('sender_id')
        receiver_id = received_data.get('receiver_id')

        if not message or not userchat_id or not user_id:
            print('Error:: Incomplete message data')
            return False

        sender = await self.get_user(user_id)
        if receiver_id:
            receiver = await self.get_user(receiver_id)
        else:
            receiver = None
        userchat_obj = await self.get_userchat(userchat_id)
        if not sender:
            print('Error:: sent by user is incorrect')
        if not userchat_obj:
            print('Error:: UserChat id is incorrect')

        message_obj = await self.save_message(sender, message, userchat_obj)

        is_group_chat = await self.userchat_has_group(userchat_obj)
        if not is_group_chat:
            other_user_chat_room = f'user_chatroom_{receiver_id}'
            self_user = self.scope['user']
            response = {
                'message': message,
                'sent_by': str(self_user.id),
                'userchat_id': userchat_id,
                'send_time': message_obj.timestamp.strftime("%d %a, %H:%M"),
                'username': await self.get_username(message_obj.user),
                'user_photo': await self.get_user_photo(message_obj)
            }
            print(response)
            await self.channel_layer.group_send(
                other_user_chat_room,
                {
                    'type': 'chat_message',
                    'text': json.dumps(response)
                }
            )

            await self.channel_layer.group_send(
                self.chat_room,
                {
                    'type': 'chat_message',
                    'text': json.dumps(response)
                }
            )
        else:
            group_id = await self.get_group_id(userchat_obj)
            members = await self.get_group_members(group_id)
            for user in members:
                user = await user
                other_user_chat_room = f'user_chatroom_{user.id}'
                self_user = self.scope['user']
                response = {
                    'message': message,
                    'sent_by': str(self_user.id),
                    'userchat_id': userchat_id,
                    'send_time': message_obj.timestamp.strftime('%d %a, %H:%M'),
                    'username': self.get_username(message_obj.user),
                    'user_photo': await self.get_user_photo(message_obj)
                }

                if user != sender:
                    await self.channel_layer.group_send(
                        other_user_chat_room,
                        {
                            'type': 'chat_message',
                            'text': json.dumps(response)
                        }
                    )
                else:
                    await self.channel_layer.group_send(
                        self.chat_room,
                        {
                            'type': 'chat_message',
                            'text': json.dumps(response)
                        }
                    )

    async def websocket_disconnect(self, event):
        await self.channel_layer.group_discard(
            self.chat_room,
            self.channel_name
        )

    async def chat_message(self, event):
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    async def send_group_message(self, user_id, message, userchat):
        # Ensure this operation is performed asynchronously
        members = await self.get_group_members(userchat.group.id)
        for member in members:
            if member.id != user_id:
                await self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({
                        'message': message,
                        'sent_by': user_id,
                        'userchat_id': userchat.id
                    })
                })

    @database_sync_to_async
    def get_userchat(self, userchat_id):
        return UserChat.objects.filter(id=userchat_id).first()

    @database_sync_to_async
    def userchat_has_group(self, userchat_obj):
        return userchat_obj.group is not None

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.filter(id=user_id).first()

    @database_sync_to_async
    def save_message(self, user, message, userchat):
        user_profile = UserProfile.objects.get(user=user)
        return ChatMessage.objects.create(user=user_profile, userchat=userchat, message=message)

    @database_sync_to_async
    def get_group_members(self, group_id):
        group = ChatGroup.objects.filter(id=group_id).first()
        if group:
            members = group.members.all()
            users = [self.get_user(member.user.id) for member in members]
            return users
        return []

    @database_sync_to_async
    def get_group_id(self, userchat_obj):
        return userchat_obj.group.id

    @database_sync_to_async
    def get_username(self, user):
        return user.user.username

    @database_sync_to_async
    def get_user_photo(self, chat):
        if chat.user.profile_photo is not None:
            return chat.user.profile_photo.url
        else:
            return None
