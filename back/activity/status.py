from django.contrib.auth.models import User
from users.models import Profile

class Status:
	@staticmethod
	def getStatus(user: User):
		uProfile: Profile = user.Profile
		state = uProfile.state

		if uProfile.isPlaying:
			return ("In-game")
		match state:
			case 0:
				return ("Offline")
			case 1:
				return ('Online')
	
	@staticmethod
	def warnFriends(friendsOf: User, content: str):
		from .consumers import ActivityConsumer
		uProfile: Profile = friendsOf.Profile
		
		for f in uProfile.friends.all():
			ActivityConsumer.sendMessageToConsumer(f.username, {
				'user': uProfile.getUsername(),
				'state': content
			}, 'state')

	@staticmethod
	def warnFriend(warner: User, target: User, content: str):
		from .consumers import ActivityConsumer
		ActivityConsumer.sendMessageToConsumer(target.username, {
			'user': warner.username,
			'state': content,
		}, 'state')

	@staticmethod
	def connect(user: User):
		uProfile: Profile = user.Profile
		uProfile.setState(1)
		Status.warnFriends(user, 'Online')
		Status.getFriendsStatus(user)

	@staticmethod
	def disconnect(user: User):
		uProfile: Profile = user.Profile
		uProfile.setState(0)
		Status.warnFriends(user, 'Offline')

	@staticmethod
	def inGame(user: User):
		Status.warnFriends(user, 'In-game')

	@staticmethod
	def leaveGame(user: User):
		Status.warnFriends(user, 'Online')
		
	@staticmethod
	def getFriendsStatus(user: User):
		from .consumers import ActivityConsumer
		uProfile: Profile = user.Profile
		statuses = {}
		
		for f in uProfile.friends.all():
			statuses[f.username] = Status.getStatus(f)
		
		for key, value in statuses.items():
			data = {
				'user': key,
				'state': value	
			}
			ActivityConsumer.sendMessageToConsumer(uProfile.getUsername(), data, 'state')