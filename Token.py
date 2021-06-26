from luv.Coordinate import Coordinate
import luv.Action as Action
import luv.Enums as Enums
from copy import deepcopy
from collections import defaultdict
# all posible moving directions for a token
ALL_DIRECTIONS = [(0, -1), (-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1)]

TARGETS = {Enums.TokenType.S: Enums.TokenType.P, Enums.TokenType.P: Enums.TokenType.R, Enums.TokenType.R: Enums.TokenType.S}
ENEMIES = {Enums.TokenType.S: Enums.TokenType.R, Enums.TokenType.R: Enums.TokenType.P, Enums.TokenType.P: Enums.TokenType.S}

class Token:
	position: Coordinate
	team: Enums.Team
	#ttype: str
	ttype: Enums.TokenType

	def __init__(self, position, team, ttype):
		self.position = Coordinate(position[0], position[1])
		self.team = team
		self.tokenType = ttype

		# Protect against passing a string for ttype instead of an Enum type
		if ttype == 's':
			self.tokenType = Enums.TokenType.S
		if ttype == 'r':
			self.tokenType = Enums.TokenType.R
		if ttype == 'p':
			self.tokenType = Enums.TokenType.P

	
	def distance(self, other):
		"""
		Distance between two tokens.
		"""
		return self.position.distance(other.position)

	def toString(self):
		return "(tokenType: " +  str(self.tokenType) + ", position:" + self.position.toString() +")"


	def getTokenActions(self, tokens):
		"""
		Get possible valid move actions for the token.
		:param tokens: all tokens in the team
		"""
		# get all slide hexes
		slide_hexes = [self.getSlideCoordinates(direction) for direction in ALL_DIRECTIONS]
		swing_hexes = []

		# get all swing actions regardless of validity
		neighbouring_hexes = slide_hexes
		for token in tokens:
			for neighbouring_hex in neighbouring_hexes:
				# check for tokens in neighbouring hexes
				# if one of its team members in its neighbourhood, then token can swing
				if token.position == neighbouring_hex:
					new_swings = [token.getSlideCoordinates(direction) for direction in ALL_DIRECTIONS]
					for new_swing in new_swings:
						# don't append moves that are already in the list
						if new_swing not in swing_hexes and new_swing not in slide_hexes:
							swing_hexes.append(new_swing)

		# remove the current position of the token from the list
		if self.position in swing_hexes:
			swing_hexes.remove(self.position)


		actions = [Action.SlideAction(self, slide_hex) for slide_hex in slide_hexes]
		actions.extend([Action.SwingAction(self, swing_hex) for swing_hex in swing_hexes])

		# remove invalid actions
		actions = [action for action in actions if action.isValid()]
		return actions

	
	def getLimitedTokenActions(self, player_tokens, opponent_tokens, num_actions):
		"""
		Filter our the action for the tokens and return.
		< We later decided to change from get limited token's actions to get limited actions of the whole board >
		"""
		# get all the actions the token can make
		actions = self.getTokenActions(self, player_tokens)
		# return the actions list if we already have an acceptable amount
		if len(actions) <= num_actions:
			return actions

		# create a dictionary that stores the distance between this token and its nearest target 
		token_cpy = deepcopy(self)
		post_dis_dic = defaultdict(int)
		for action in actions:
			token_cpy.position = action.to_point
			post_dis_dic[action] = token_cpy.distanceToNearestTarget(opponent_tokens)

		actions_sorted = sorted(post_dis_dic, key = post_dis_dic.get, ascending=True)
		return actions[0:num_actions]


	def distanceToNearestTarget(self, opponent_tokens):
		'''
		Note to add checks if other player tokens are closer to our nearest target
		to avoid two tokens going for the same opponent token
		'''
		return min(self.distance(x) for x in opponent_tokens if TARGETS[self.tokenType] == x.tokenType)

	def getSlideCoordinates(self, direction):
		''' 
		Finds and returns the hex coordinates to which the token will slide in the given direction. 
		Does not check if the slide is valid (off the board, enemy tokens)
		:param direction: (dx, dy)
		'''

		delta_x, delta_y = direction
		return Coordinate(self.position.x + delta_x, self.position.y + delta_y)


	def update(self, x_to, y_to):
		"""
		Update the token to a new position
		"""

		self.position = Coordinate(x_to, y_to)


	def defeated(self, tokens):
		"""
		Check whether the token is defeated.
		"""
		for token in tokens:
			if token.tokenType == ENEMIES[self.tokenType]:
				return True

		return False

	def get_nearest_target(self, others):
		""" Return the nearest target."""
		# set min_dist to be greater than the largest possible distance on the board
		min_dist = 10
		for opponent in others:
			if TARGETS[self.tokenType] == opponent.tokenType:
				dist = self.position.distance(opponent.position)
				if dist < min_dist:
					min_dist = dist
					target = opponent

		# if a token has no targets, its distance should be 0
		if min_dist == 10:
			return None
		return target

	
