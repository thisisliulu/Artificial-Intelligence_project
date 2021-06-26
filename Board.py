import luv.Enums as Enums
from luv.util import print_board
import luv.Token as Token
from luv.Team import Team
from collections import defaultdict
from luv.Token import TARGETS, ENEMIES
from luv.util import print_board
from copy import copy
from copy import deepcopy
from luv.Coordinate import Coordinate
import random
import time

from copy import deepcopy
import numpy as np

UNASSIGNED = -np.inf

WIN = 1
LOSE = -1
DRAW = 0
TOTAL_SYMBOLS = 3
class Board:
	team: Enums.Team
	depth: int
	def __init__(self, team, parent):
		self.uppers = Team(Enums.Team.UPPER)
		self.lowers = Team(Enums.Team.LOWER)

		# utility for upper player
		self.utility = UNASSIGNED
		self.parent = parent
		# which side of team are we in  
		self.team = team
		self.isFullyExpand = False
		# {child: (upper_action, lower_action), child2: (upper_action, lower_action)}
		self.child = {}
		if not self.parent:
			self.depth = 0
		else:
			self.depth = self.parent.depth + 1
		# self.eval = self.evaluation_score()

	def print_Board(self):
		"""
		To print the board configuration.
		"""
		board_dict = {}
		no_uppers = self.uppers.isEmpty()
		no_lowers = self.lowers.isEmpty()
		if self.checkEmpty():
			print_board(board_dict)
			return 
		if no_uppers:
			print_board(self.lowers.to_dict())
			return
		if no_lowers:
			print_board(self.uppers.to_dict())
			return
		board_dict = self.uppers.to_dict()
		board_dict.update(self.lowers.to_dict())
		print_board(board_dict)
		return 
		
	def toString(self):
		return "board: {uppers: " + self.uppers.toString() + ", lowers: " + self.lowers.toString() + ", self team: " + str(self.team) + ", depth: " + str(self.depth) + "}"

	def __eq__(self, other):
		return self.uppers == other.uppers and (self.lowers == other.lowers)
	
	def __hash__(self):
		#return hash(self.uppers.__hash__, self.lowers.__hash__)
		return hash(self.uppers.__hash__) + hash(self.lowers.__hash__)
	
	def evaluation_score(self):
		#return hash(self.uppers) + hash(self.lowers)
		# average distance between each upper token and its nearest target
		# need to deal with tokens that don't have a nearest and tokens that are targeting the same token
		total_dist = 0
		for upper in self.uppers.team:
			lower = upper.get_nearest_target(self.lowers.team)
			if lower:
				total_dist += upper.position.distance(lower.position)
		if  len(self.uppers.team) == 0:
			avg_upper_dist = 0
		else:
			avg_upper_dist = total_dist / len(self.uppers.team)

		# average distance between each upper token and its nearest target
		# need to deal with tokens that don't have a nearest and tokens that are targeting the same token
		total_dist = 0
		for lower in self.lowers.team:
			upper = lower.get_nearest_target(self.uppers.team)
			if upper:
				total_dist += lower.position.distance(upper.position)
		if len(self.lowers.team) == 0:
			avg_lower_dist = 0
		else:
			avg_lower_dist = total_dist / len(self.lowers.team)
		
		return avg_upper_dist- avg_lower_dist

	
	def goal_test(self):
		"""
		This function is based on the 'def _turn_detect_end(self):' in the referee.game file.
		To detect whether it is an end of the game.
		"""
		upper_tokens = [s for s in self.uppers.team]
		lower_tokens = [s for s in self.lowers.team]
		upper_typeset = set([s.tokenType for s in upper_tokens])
		lower_typeset = set([s.tokenType for s in lower_tokens])
		upper_inv = [s for s in upper_tokens if self.lowers.remaining_throws == 0 and not s.defeated(lower_tokens)]
		lower_inv = [s for s in lower_tokens if self.uppers.remaining_throws == 0 and not s.defeated(upper_tokens)]
		upper_notokens = self.uppers.remaining_throws == 0 and len(upper_tokens) == 0
		lower_notokens = self.lowers.remaining_throws == 0 and len(lower_tokens) == 0
		upper_onetoken = self.uppers.remaining_throws == 0 and len(upper_tokens) == 1
		lower_onetoken = self.lowers.remaining_throws == 0 and len(lower_tokens) == 1

		# condition 1
		if upper_notokens and lower_notokens:
			self.utility =  DRAW
			return True
		if upper_notokens:
			self.utility = LOSE
			return True
		if lower_notokens:
			self.utility = WIN
			return True
		
		# condition 2: both have invincible
		if upper_inv and lower_inv:
			self.utility = DRAW
			return True
		
		# condition 3: one has an invincible token and the other has only one remaining token 
		if upper_inv and lower_onetoken:
			self.utility = WIN
			return True
		if lower_inv and upper_onetoken:
			self.utility = LOSE
			return True
		
		# condition 5
		if self.depth >= 360:
			self.utility =  DRAW
			return True
		self.utility = UNASSIGNED
		return False

	def checkEmpty(self):
		"""
		To check whether the board is empty. 
		If the board is empty(for both uppers and lowers), then it is the start of the game.
		"""
		return self.uppers.isEmpty() and self.lowers.isEmpty()
	

	def result(self, action, player):
		"""
		Give an action from a team, result in a new child board.
		Since it is just one side action, then the depth should increase by 0.5.
		param:
			action: Action
			player: which player do this action
		"""
		childboard = deepcopy(self)
		if player == Enums.Team.UPPER:
			childboard.uppers.update(action.represent())
		else:
			childboard.lowers.update(action.represent())
		# if the action is not 
		childboard.checkCollision([action.to_point])
		childboard.parent = self
		childboard.depth = self.depth + 0.5
	
		return childboard

	def update_board(self, upper_action, lower_action):
		"""
		Accept the upper action and lower action, check collision and return the updated board.
		parameters:
		upper_action: a tuple representation of upper player's action
		lower_action: a tuple representation of lower player's action
		"""
		newboard = Board(self.team, self)
		newboard.uppers = deepcopy(self.uppers)
		newboard.lowers = deepcopy(self.lowers)
		newboard.uppers.update(upper_action)
		newboard.lowers.update(lower_action)
		_, _, (r1, q1) = upper_action
		_, _, (r2, q2) = lower_action
		
		# if the upper and lower player move to the same position, then just need to check that position, otherwise need to check two risk hexes
		if r1 == r2 and q1 == q2:
			collision_risk_hexes = [Coordinate(r1, q1)]
		else:
			collision_risk_hexes = [Coordinate(r1, q1), Coordinate(r2,q2)]
			# board needs to check collision
		# within each team or between player and opponent
		newboard.checkCollision(collision_risk_hexes)
		return newboard

	def getActions(self,ttype, action_limit):
		"""
		Given teamType, board will get possible actions from the team.
		parameters:
		ttype: UPPER or LOWER, refer to a special team
		action_limit: an int that limits the number of actions returned
		"""
		if ttype == Enums.Team.UPPER:
			opponent_tokens = self.lowers.team
			actions = self.uppers.getLimitedActions(opponent_tokens, action_limit)
			
		else:
			opponent_tokens = self.uppers.team
			actions = self.lowers.getLimitedActions(opponent_tokens, action_limit)
			
		return actions

	
	def checkCollision(self, hexes):
		"""
		Check collision on the board when the board is updated.
		parameters:
		hexes: a list of hexes, of which collision may happen.
		"""
		destroyed_tokens = []
		for position in hexes:
			colliding_tokens = []

			# collect for each hex, type of token and its number
			symbols = []
			# collect upper tokens on the hex
			for token in self.uppers.team:
				if token.position.distance(position) == 0:
					colliding_tokens.append(token)
					if token.tokenType not in symbols:
						symbols.append(token.tokenType)
			# collect lower tokens on the hex
			for token in self.lowers.team:
				if token.position.distance(position) == 0:
					colliding_tokens.append(token)
					if token.tokenType not in symbols:
						symbols.append(token.tokenType)
		
			# if the hex is occupied by one or more tokens with each symbol, all of the tokens are defeated
			if len(symbols) == TOTAL_SYMBOLS:
				destroyed_tokens.extend(colliding_tokens)
			# all the tokens are the same type
			elif len(symbols) == 1:
				pass
		
			# tokens in the hex contain two symbols
			else: 
				# symbol 0 wins
				if TARGETS[symbols[0]]== symbols[1]:
					filter_colliding = list(filter(lambda x: x.tokenType == symbols[1],colliding_tokens))
					destroyed_tokens.extend(filter_colliding)
				# symbol 1 wins
				else: 
					filter_colliding = list(filter(lambda x: x.tokenType == symbols[0],colliding_tokens))
					destroyed_tokens.extend(filter_colliding)

		# remove the destroyed tokens
		for token in destroyed_tokens:
			if token.team == Enums.Team.UPPER:
				self.uppers.team.remove(token)
			else:
				self.lowers.team.remove(token)

