from django.db import models
from blockchain.models import Contract, ContractBuilder
from coordination.tools import setInMatch, setOutMatch
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from uuid import uuid4
from django.contrib.postgres.fields import ArrayField
from threading import Thread
import time
import shortuuid
import sys

def roomIdGenerator():
	uuid = shortuuid.uuid()[:8]
	uuid = uuid.upper()

	if Room.objects.filter(id=uuid).exists():
		return roomIdGenerator()
	return uuid

class Match(models.Model):
	"""
	The score is scored as the order
	score[0] = host
	score[1] = invited
	"""
	def default_ready():
		return ([False, False])

	host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='host', blank=False)
	invited = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invited', blank=False)
	id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
	duration = models.DurationField(default=timedelta(minutes=0))
	contract = models.ForeignKey(Contract, null=True, default=None, on_delete=models.CASCADE)
	winner = models.ForeignKey(User, default=None, null=True, on_delete=models.CASCADE)
	date = models.DateTimeField(auto_now_add=True)
	state = models.IntegerField(default=0) # 0 waiting, 1 started, 2 finish
	ready = ArrayField(models.BooleanField(), size=2, default=default_ready)
	start_time = models.DateTimeField(auto_now_add=True)
	creation_date = models.DateTimeField(auto_now_add=True)
	data = models.JSONField(null=True, default=None)

	@staticmethod
	def speakConsumer(speaker: User, content: str):
		if not speaker.Profile.isPlaying:
			return
		currentMatch = Match.getMatch(user=speaker)
		if not currentMatch:
			return
		currentMatch.speak(speaker, content)

	@staticmethod
	def getMatch(**kwargs):
		"""
		This value can be an user or a Match ID (user, id)
		"""
		id = kwargs.get('id')
		user = kwargs.get('user')
		if (id):
			return Match.objects.filter(id=id).first()
		elif (user):
			return Match.objects.filter(Q(host=user, state=1) | Q(invited=user, state=1)).first()

	@staticmethod
	def create(host: User, invited: User) -> str:
		match = Match.objects.create(host=host, invited=invited)
		return match.id

	@staticmethod
	def historic(user: User, since, n=50, object=False) -> list:
		matchs = Match.objects.filter(Q(host=user, date__gte=since) | Q(invited=user, date__gte=since)).filter(state=2).order_by('-creation_date')[:n]
		if object:
			return matchs
		return [m.toJson() for m in matchs]

	def speak(self, sender: User, content: str):
		if sender != self.host and sender != self.invited:
			return
		target = self.host if sender == self.invited else self.invited
		if (self.state != 2): # Avoid old mate to come
			r = self.room()
			if (r):
				self.room().send(target, 'chat', {"from": sender.username, "content": content, 'sendAt': str(timezone.now())})
	
	def send(self, user: User, event: str, data: str, delay = 0):
		from coordination.consumers import CoordinationConsumer
		if user != self.host and user != self.invited:
			return
		else:
			CoordinationConsumer.sendMessageToConsumer(user.username, data, event, delay)

	def room(self):
		return Room.objects.filter(matchs=self).first()

	@staticmethod
	def wait(match_id, host_username, invited_username):
		"""
		Needed before the match start to wait for the player to be ready !
		Must be runned inside a thread
		"""
		from .core import GameMap

		GameMap.createGame(str(match_id), host_username, invited_username)
		time.sleep(20)
		match = Match.getMatch(id=match_id) #actualisation !
		if (not match.ready[0] or not match.ready[1]):
			# mettre les stats a des valeurs par defaut !
			match.setStartTime(timezone.now())
			match.finish((10, 10), tap=0, duration=0, distance=0)
		return

	def start(self):
		# Tell people there next match !
		# print(f"je commence le match{self.host} {self.invited}", file=sys.stderr)
		self.setState(1)
		self.setStartTime(timezone.now())

	def finish(self, score: tuple, **kwargs):
		"""
		Function to ended a match, this will run the generation of a blockchain smart contract\n
		also run the checkup of next match if it is a tournament
		"""
		winner = self.host if score[0] > score[1] else self.invited
		room = self.room()
		self.setWinner(winner)
		loser = self.getLoser()

		ContractBuilder.threaded(score, self) # Blockchain Runner !
		self.setDuration(timezone.now() - self.start_time)
		self.setState(2)
		self.setData({'distance': kwargs['distance'], 'duration': self.duration.total_seconds(), 'pong': kwargs['tap']})  #change to real values
		setOutMatch(loser) # let free the loser

		# Statistics
		loser.stats.addResult(False)
		winner.stats.addResult(True)

		if room:
			room.addEliminated(loser)
			# here make the room update and check for the next match !
			room.update()

	def getWinner(self) -> User:
		if self.winner == self.host:
			return self.host
		return self.invited

	def getLoser(self) -> User:
		if self.winner != self.host:
			return self.host
		return self.invited
	
	def setWinner(self, winner: User):
		self.winner = winner
		self.save()

	def setState(self, state: int):
		self.state = state
		self.save()

	def setDuration(self, duration):
		self.duration = duration
		self.save()

	def setStartTime(self, time):
		self.start_time = time
		self.save()

	def setData(self, tab):
		self.data = tab
		self.save()

	def getScore(self):
		if not self.contract:
			return (10, 10)
		else:
			return (self.contract.getScore())

	def setScore(self, score):
		self.contract = score
		self.save()

	def toJson(self) -> dict | None:
		if (self.state != 2):
			return None
		else:
			return {
				'id': self.id,
				'host': self.host.username,
				'invited': self.invited.username,
				'score': self.getScore(),
				'duration': self.duration.seconds,
				'winner': self.getWinner().username,
				'distance': round(self.data['distance']),
				'date': self.creation_date,
				}
		
	
class Mode():
	CLASSIC = '2', 'classic'
	INVITATION = '2', 'invitation'
	TOURNAMENT4 = '4', 'tournament4'
	TOURNAMENT8 = '8', 'tournament8'
	TOURNAMENT16 = '16', 'tournament16'

	labels = (CLASSIC[1], INVITATION[1], TOURNAMENT4[1], TOURNAMENT8[1], TOURNAMENT16[1])

	@staticmethod
	def fromText(modestr: str):
		modestr = modestr.upper()
		for mode in Mode.labels:
			if mode.upper() == modestr:
				return getattr(Mode, modestr)
		return Mode.CLASSIC

class Room(models.Model):
	# Mode class for the type of the room
	
	"""
	A room is multiples players that choosen to player together
	that means that a room can contain multiples matchs (so it's called a tournament).
	"""
	opponents = models.ManyToManyField(User, related_name='opponents')
	eliminated = models.ManyToManyField(User, related_name='eliminated')
	closed = models.ManyToManyField(User, related_name='closed')
	numberMatchsLastRound = models.IntegerField(default=0)
	state = models.IntegerField(default=0) # 0 waiting, 1 started, auto delete when finish
	id = models.CharField(primary_key=True, default=roomIdGenerator, blank=False, max_length=8)
	matchs = models.ManyToManyField(Match, related_name='matchs')
	winner = models.ForeignKey(User, null=True, default=None, on_delete=models.CASCADE)
	mode = ArrayField(models.CharField(max_length=30, blank=False), 2)

	"""
	function a coder
	createRoom() | OK
	joinRoom(user) -> checker si la rooom et pas full 
	addPlayer(suer) - > OK
	runRoom(user) -> permet de lancer la room
	getNextMatch(user) -> permet de générer le prochain match !
	"""
	
	def _runRoom(self):
		if (self.opponents.count() != int(self.mode[0])): #mean that there isn't enought of players
			return
		# print(f"la room doit commencer \nVoici les adversaires : {self.opponents.all()}", file=sys.stderr)
		self.state = 1
		self.save()

		for player in self.opponents.all():
			setInMatch(player)
			if self.mode[1] != Mode.CLASSIC[1]:
				player.stats.addTournament()

		self.next_server(True)
	
	def removePlayer(self, player: User):
		"""
		Return 0 in case of success then 1
		"""
		if (self.state != 0):
			return 1
		if (player in self.opponents.all()):
			self.opponents.remove(player)
			
			if (self.opponents.count() == 0):
				self.delete()
			else:
				self.updateCountsAll(player)
				self.save()
			return 0

	def send(self, user: User, event: str, data: str):
		from coordination.consumers import CoordinationConsumer
		if user not in self.opponents.all():
			return
		else:
			CoordinationConsumer.sendMessageToConsumer(user.username, data, event)

	def addPlayer(self, player: User) -> str:
		actual = self.opponents.count()
		if (player.Profile.isPlaying == True):
			return ("You are already playing !", False)
		if (actual >= int(self.mode[0])):
			return ("There is too much player in the room !", False)
		if (player in self.opponents.all()):
			return ("You already joined this room !", False)
		self.opponents.add(player)
		self.save()
		self.updateCountsAll(player)

		# function to check if roomReady !
		self.update()
		return ("You successfully join the room !", True)
	
	def next_server(self, first=False):
		"""
		Generate the next match seeds !
		And warn the player !
		"""
		matchOpponents = []
		if first: # first round
			nPlayer = self.opponents.count()
			players = list(self.opponents.all())
			for i in range(0, nPlayer, 2):
				matchOpponents.append(players[i:i+2])

		else:
			if self.numberMatchsLastRound == 1:
				# end of the tournament
				lastMatch: Match = self.matchs.all().order_by('-creation_date')[:1].get()
				setOutMatch(lastMatch.getWinner())
				self.winner = lastMatch.getWinner()
				self.save()

				if (int(self.mode[0]) == 2):
					self.addClosed(lastMatch.getLoser())
					self.addClosed(lastMatch.getWinner())
				return
			# il y a d'autres matchs à faire +_+
			lastMatchs = list(self.matchs.all().order_by('-creation_date')[:self.numberMatchsLastRound])
			winners = [m.getWinner() for m in lastMatchs]
			matchOpponents = [[winners[i], winners[i + 1]] for i in range(0, len(winners), 2)]

		matchs = [Match.getMatch(id=Match.create(opponents[0], opponents[1])) for opponents in matchOpponents]
		self.numberMatchsLastRound = len(matchs)
		self.matchs.add(*matchs)
		self.save()

		if self.mode[1] == Mode.CLASSIC[1]:
			# This is the matchmaking to skip wait
			from .core import GameMap
			classic = matchs[0]
			GameMap.createGame(str(classic.id), classic.host.username, classic.invited.username)
			classic.send(classic.invited, 'next', {'match-id': str(classic.id), 'host': classic.host.username, 'invited': classic.invited.username, 'statusHost': False}, delay=2.5)
			classic.send(classic.host, 'next', {'match-id': str(classic.id), 'host': classic.host.username, 'invited': classic.invited.username, 'statusHost': True}, delay=2.5)
			classic.ready = [True, True]
			classic.save()
			classic.start()
		else:
			# Runner the thread to wait the game (to players to be ready !)
			# print('la room est prete demander vos next \n', file=sys.stderr)
			for m in matchs:
				thread = Thread(target=m.wait, args=(m.id, m.host.username, m.invited.username))
				thread.start()

	def update(self):
		"""
		Update the tournament and send player their next match
		Check all actual matchs are ended !
		"""
		if self.state == 0:
			return self._runRoom()
		elif self.state == 1:
			# mean that this is the first round !
			if self.matchs.count() == 0:
				self.next_server(True)
			# check if all the last match has ended !
			else:
				for m in self.matchs.all():
					if m.state == 0 or m.state == 1:
						return
				return self.next_server()
			# faire les nexts matchs etc voir pour les tournois

	def updateCountsAll(self, updater: User):
		from coordination.consumers import CoordinationConsumer
		"""
		Send a message to all the player to tell them how much player there is actually in the room
		"""
		count = self.opponents.count()

		for p in self.opponents.all():
			data = {'room-id': self.id, 'count': count, 'updater': updater.username, 'max': int(self.mode[0])}
			CoordinationConsumer.sendMessageToConsumer(p.username, data, 'count')
		return
	
	def addEliminated(self, user):
		self.eliminated.add(user)
		self.save()

	def addClosed(self, user):
		self.closed.add(user)
		self.save()

		if self.closed.count() == self.opponents.count():
			return self.delete()

	def getRank(self, user):
		eliminated = list(self.eliminated.all())
		return (self.opponents.count() - eliminated.index(user))

	@staticmethod
	def createRoom(owner: User, mode = Mode.CLASSIC):
		"""
		This function create a room and return the object !
		Owner will be the first player to join the room
		Mode must be a value from Room.Mode
		"""
		room = Room.objects.create(mode=[mode[0], mode[1]])
		room.opponents.add(owner)
		room.save()
		room.updateCountsAll(owner)
		return room
	
	@staticmethod
	def createRoomConsumer(owner: User, mode = Mode.CLASSIC):
		"""
		This fonction return the room code or an error 
		Check if user already in a room or matchmaking queue
		"""
		from coordination.tools import isAvailableToPlay

		check = isAvailableToPlay(owner)
		if not (check[1]):
			return check
		room = Room.createRoom(owner, mode)
		return (room.id, True)
	
	@staticmethod
	def getRoom(roomId: str):
		"""
		If roomID doesn't exist the value returned is None
		"""
		room = Room.objects.filter(id=roomId).first()
		return (room)

	@staticmethod
	def joinRoom(player: User, code: str) -> tuple:
		from coordination.tools import isAvailableToPlay
		targetRoom: Room = Room.getRoom(code)
		check = isAvailableToPlay(player)

		if not (check[1]):
			return check 
		if not targetRoom:
			return ("Room is inexisting !", False)
		else:
			return targetRoom.addPlayer(player)

	@staticmethod
	def leaveRoom(player: User, code: str) -> tuple:
		targetRoom: Room = Room.getRoom(code)
		if not targetRoom:
			return ("Room is inexisting !", False)
		else:
			match targetRoom.removePlayer(player):
				case 1:
					return (f"Room is already launched can't leave !", False)
				case 0: #success !
					return (f"Succefully left the room {code}", True)
	
	@staticmethod
	def disconnectAPlayer(player: User):
		"""
		This will the player from all the waiting room !
		"""
		from game.core import GameMap

		playerRooms = Room.objects.filter(opponents=player, state=0).all()
		for room in playerRooms:
			room.removePlayer(player)

		activeRoom = Room.getRoomFromPlayer(player)
		if activeRoom:
			activeRoom.addClosed(player)

		activeGame = Match.getMatch(user=player)
		if activeGame:
			GameMap.removeGame(activeGame.id)
	
	@staticmethod
	def isInWaitingRoom(player: User) -> bool:
		"""
		If player waiting in a room
		"""
		room = Room.objects.filter(opponents=player, state=0).first()
		return room.id if room else False

	@staticmethod
	def getRoomFromPlayer(player: User):
		return Room.objects.filter((Q(state=1, opponents=player) | Q(state=0, opponents=player)) & ~Q(closed=player)).first()

	@staticmethod
	def next_client(player: User, room_id: str):
		"""
		Tell the client it's next match
		"""
		room = Room.getRoom(room_id)
		if not room:
			room = Room.getRoomFromPlayer(player)
		if room:
			if player in room.closed.all():
				return
			if player in room.eliminated.all():
				# print(f"j'envoie le message end à {player.username}", file=sys.stderr)
				room.send(player, 'end', {'room-id': room.id, 'rank': room.getRank(player)})
				room.addClosed(player)
				return
			if player == room.winner:
				room.send(player, 'win', {'room-id': room.id})
				room.addClosed(player)
				return
			matchsRunning = list(room.matchs.all().order_by('-creation_date')[:room.numberMatchsLastRound])
			for m in matchsRunning:
				if m.host == player or m.invited == player:
					who = 0 if m.host == player else 1
					if m.ready[who] == True or m.state != 0:
						return
					m.ready[who] = True
					m.save()
					if who:
						m.send(m.invited, 'next', {'match-id': str(m.id), 'host': m.host.username, 'invited': m.invited.username, 'statusHost': False}, delay=2.5)
					else:
						m.send(m.host, 'next', {'match-id': str(m.id), 'host': m.host.username, 'invited': m.invited.username, 'statusHost': True}, delay=2.5)
					if (m.ready[0] and m.ready[1]):
						m.start()
					return