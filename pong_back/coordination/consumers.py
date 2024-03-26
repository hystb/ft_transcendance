from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from activity.tools import getChannelName
from users.models import Profile
from django.contrib.auth.models import User
from .matchmaking import Matchmaking
from .invitations import InvitationStack
from channels.layers import get_channel_layer
from game.models import Room, Mode, Match

class CoordinationConsumer(AsyncJsonWebsocketConsumer):
		
	@database_sync_to_async
	def getUsername(self):
		return (self.user.username)

	@database_sync_to_async
	def getUser(self, username=None) -> User:
		tUser = self.user.username if not username else username
		return (Profile.getUserFromUsername(tUser))
	
	@database_sync_to_async
	def desactivePlaying(self):
		self.user.profile.setPlaying(False)

	async def connect(self):
		self.user = self.scope['user']
		await self.accept()
		await self.channel_layer.group_add(getChannelName(await self.getUsername(), 'coord'), self.channel_name)

	async def disconnect(self, code):
		# need to leave the matchmaking queue
		await sync_to_async(Matchmaking.removePlayerToQueue)(self.user)

		# need to leave all the rooms not launched | and change state to is playing to None
		await database_sync_to_async(Room.disconnectAPlayer)(self.user)
		await self.desactivePlaying()

		await self.channel_layer.group_discard(getChannelName(await self.getUsername(), 'coord'), self.channel_name)
		return await super().disconnect(code)
	
	async def messageResponse(self, event: str, values: tuple):
		"""
		values[0] is the message
		values[1] is code -> success (True), failure (False)
		"""
		await self.send_json({'event': event, 'data': {'message': values[0], 'status': values[1]}})


	async def send_message(self, event):
		await self.send_json(content={
			'event': event['event'],
			'data': event['data'] 
		})
	
	async def receive_json(self, content: dict, **kwargs):
		if 'event' in content and 'data' in content:
			data = content['data']
			user = await self.getUser()
			target = data.get('target')
			match content['event']:
				# to request some matchmaking !
				case 'matchmaking':
					if 'action' in data:
						match data['action']:
							case 'join':
								await self.messageResponse('matchmaking', await sync_to_async(Matchmaking.addPlayerToQueue)(user))
							case 'quit':
								await self.messageResponse('matchmaking', await sync_to_async(Matchmaking.removePlayerToQueue)(user))
				case 'next':
					if 'room-id' in data:
						await sync_to_async(Room.next_client)(user, data['room-id'])
				# to join a private tournament !
				case 'tournament':
					if 'action' in data and 'room-id' in data:
						match data['action']:
							case 'join':
								await self.messageResponse('tournament', await sync_to_async(Room.joinRoom)(user, data['room-id']))
							case 'quit':
								await self.messageResponse('tournament', await sync_to_async(Room.leaveRoom)(user, data['room-id']))
				# case to create a private tournament
				case 'create':
					if 'mode' in data:
						await self.messageResponse('create', await sync_to_async(Room.createRoomConsumer)(user, mode=Mode.fromText(data['mode'])))
				# in game chat !
				case 'chat':
					if 'content' in data:
						# handle le chat message !
						await sync_to_async(Match.speakConsumer)(user, data.get('content'))	
				# For invitation game (1v1 friends)
				case 'invite':
					if target:
						await self.messageResponse('invite', await sync_to_async(InvitationStack.invite)(await self.getUser(), await self.getUser(username=target)))
				case 'accept':
					if target:
						await self.messageResponse('accept', await sync_to_async(InvitationStack.accept)(await self.getUser(username=target), await self.getUser()))
				case 'refuse':
					if target:
						await self.messageResponse('refuse', await sync_to_async(InvitationStack.refuse)(await self.getUser(username=target), await self.getUser()))

	@staticmethod
	def sendMessageToConsumer(username: str, content: str, event: str):
		channel_layer = get_channel_layer()
		async_to_sync(channel_layer.group_send)(getChannelName(username, 'coord'),
			{
				"type" : "send.message",
				"data" : content,
				"event" : event
			}
		)