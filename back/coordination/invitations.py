import coordination.consumers as CC
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from game.models import Room, Mode
from .tools import isAvailableToPlay
import sys

class Invitation:
	def __init__(self, initier: User, target: User):
		self.timestamp = timezone.now()
		self.initier = initier
		self.target = target
		return

	def notify(self, who: str, event: str, content: str, status: bool):
		match who:
			case 'initier':
				CC.CoordinationConsumer.sendMessageToConsumer(self.initier.username, {'message':content, 'status': status}, event)
			case 'target':
				CC.CoordinationConsumer.sendMessageToConsumer(self.target.username, {'message':content, 'status': status}, event)
			case 'all':
				CC.CoordinationConsumer.sendMessageToConsumer(self.initier.username, {'message':content, 'status': status}, event)
				CC.CoordinationConsumer.sendMessageToConsumer(self.target.username, {'message':content, 'status': status}, event)
			
	def expired(self, now) -> bool:
		delta: timedelta = now - self.timestamp
		return True if delta.seconds > 30 else False
 
#invitation stack that will contain all the current invitation
class InvitationStack:
	stack = []

	@staticmethod
	def find(initier: User, target: User) -> Invitation | None:
		for invitation in InvitationStack.stack:
			if (invitation.initier == initier and invitation.target == target):
				return (invitation)
		return (None)

	@staticmethod
	def invite(initier: User, target: User) -> tuple:
		InvitationStack.update()
		
		if (initier.username == target.username):
			return ("Can't play with your self", False)
		# check doublon
		for invitation in InvitationStack.stack:
			if (invitation.initier == initier):
				return ("You already invited somebody please wait at least 30 seconds between each invite !", False)
		# check if they are friend
		if not (initier.Profile.is_friend(target)):
			return ("You must be friend with this person to do that !", False)
		
		newInvitation = Invitation(initier, target)
		InvitationStack.stack.append(newInvitation)
		newInvitation.notify('target', 'invited', ["You received an invitation from " + initier.username, initier.username], True)
		return (["Match invitation succefully send !", target.username], True)
	
	@staticmethod
	def refuse(initier: User, target: User) -> tuple:
		InvitationStack.update()
		"""
		Target is the person who refuse the invitation !
		"""
		inv: Invitation = InvitationStack.find(initier, target)
		if inv:
			inv.notify('initier', 'refuse', ["Invitation refused !", target.username], True)
			InvitationStack.stack.remove(inv)
			return (["You refused an invitation !", initier.username], True)				
		return ("This invitation do not exist anymore !", False)
	
	@staticmethod
	def accept(initier: User, target: User) -> tuple:
		InvitationStack.update()
		"""
		Target is the person who accept the invitation !
		"""
		inv: Invitation = InvitationStack.find(initier, target)
		if inv:
			InvitationStack.stack.remove(inv)

			initierCheck = isAvailableToPlay(initier)
			targetCheck = isAvailableToPlay(target)

			if not initierCheck[1] or not targetCheck[1]: # Here to avoid multi-playing
				inv.notify('target', 'refuse', "Something bad happend you can't play together !", False)
				return (["Something bad happend you can't play together"], False)
			

			# create match here !!
			room: Room = Room.createRoom(initier, Mode.INVITATION)
			room.addPlayer(target)
			inv.notify('initier', 'accept', ["Invitation accepted !", target.username, room.id] , True)
			return (["Invitation successfully accepted", initier.username, room.id], True)
		return ("This invitation do not exist !", False)
	
	@staticmethod
	def update():
		current = timezone.now()
		for invitation in InvitationStack.stack:	
			if invitation.expired(current):
				InvitationStack.stack.remove(invitation)