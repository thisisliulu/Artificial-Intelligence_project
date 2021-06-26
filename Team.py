import luv.Enums as Enums
from luv.Token import Token
from luv.Coordinate import Coordinate
import luv.Action as Action
from collections import defaultdict
from copy import deepcopy
INITIAL_THROW = 9
BOARD_SIDE_LENGTH = 4
MAX_DIS = 10
#TOKEN_TYPE = ['s', 'r', 'p']
TOKEN_TYPE = [Enums.TokenType.S, Enums.TokenType.R, Enums.TokenType.P]


TARGETS = {Enums.TokenType.S: Enums.TokenType.P, Enums.TokenType.P: Enums.TokenType.R, Enums.TokenType.R: Enums.TokenType.S}
ENEMIES = {Enums.TokenType.S: Enums.TokenType.R, Enums.TokenType.R: Enums.TokenType.P, Enums.TokenType.P: Enums.TokenType.S}


class Team:
	team: list
	teamtype: Enums.Team
	remaining_throws: int

	def __init__(self,teamtype):
		self.teamtype = teamtype
		self.team = []
		self.remaining_throws = INITIAL_THROW
	def __eq__(self, other):
		return self.teamtype == other.teamtype and self.team == other.team and self.remaining_throws == other.remaining_throws

	def to_dict(self):
		if self.teamtype == Enums.Team.LOWER:
			dic = {token.position.toTuple(): token.tokenType for token in self.team}
		else:
			dic = {token.position.toTuple(): token.tokenType.upper() for token in self.team}
		return dic

	def toString(self):
		s = ""
		for token in self.team:
			s += token.toString()
		return "(team: " + str(self.teamtype) + ", tokens: "+ s + ", remaining_throws: " + str(self.remaining_throws) + ")"

	def __hash__(self):
		return hash(frozenset(self.team)) + hash(self.remaining_throws)

	def isEmpty(self):
		"""
		Check whether the team is empty.
		"""
		return not self.team

	def group_team(self):
		groups = defaultdict(list)
		for element in self.team:
			groups[element.tokenType].append(element.position) 
		return groups

	def add_to_team(self,newToken):
		"""
		Add a new throw into the team list and remove the throws by 1.
		"""
		self.team.append(newToken)
		return 

	def remove_from_team(self, token):
		"""
		Remove a token from the team.
		"""
		self.team.remove(token)
		return

	def gettoken(self, x, y):
		"""
		Get token from the team based on position: (x,y)
		"""
		coordinate = Coordinate(x,y)
		for element in self.team:
			if element.position == coordinate:
				return element
		return None

	def getActions(self, tokenList, opponent_tokens):
		"""
		Return the possible actions for this team.
		tokenList: a list of token to get actions
		"""
		# if there are no tokens, return all throw actions
		if self.isEmpty():
			return self.getThrowActions()
		action = []
		for token in tokenList:
			#action.extend(token.getTokenActions(self.team))
			ACTIONS_PER_TOKEN = 3
			action.extend(token.getLimitedActions(self.team, opponent_tokens, ACTIONS_PER_TOKEN))

		action.extend(self.getThrowActions())
		return action

	def sortTeam(self, opponent_tokens):
		"""
		Sort a team based on the minimum distance to opponent_tokens
		opponent_tokens: a list of opponent tokens
		"""
		if self.isEmpty():
			return self.team
		dic = defaultdict(int)
		for token in self.team:
			dis = min(token.distance(x) for x in opponent_tokens)
			dic[token] = dis
		# sort a team based on their min distance to opponent
		team_sorted = sorted(dic,key = dic.get)
		return team_sorted

	def getLimitedActions(self, opponent_tokens, max_actions):
		"""
		Restrict the output action numbers.
		opponent_tokens: a list of opponent tokens
		max_actions: the maximum number of actions it can return
		"""
		# have target means the token have target to move to
		have_Target = []
		actions = self.getMoveActions()
		if actions:
			zeros = []
			escape = []
			for action in actions:
				dis = [action.to_point.distance(token.position) for token in opponent_tokens if TARGETS[action.token.tokenType] == token.tokenType]
				enemy_dis = [action.token.position.distance(enemy.position) for enemy in opponent_tokens if ENEMIES[action.token.tokenType] == enemy.tokenType]
				# avoid going to much
				if len(dis) != 0 and min(dis) <= MAX_DIS/2:
					have_Target.append(action)
				if len(dis) != 0 and min(dis) == 0:
					zeros.append(action)
				# enemy just one step
				if len(enemy_dis) != 0 and min(enemy_dis) == 1:
					escape.append(action)
			if len(zeros) > 0:
				return zeros
			# escape but avoid collision
			escape = self.filter_action(escape)
			if len(escape) > 0:
				return escape
		# to restrict the throw actions, we limit the number of throws 
		#  if the token has target on the board, then we expand the actions with limit throw
		have_Target = self.sort_actions(have_Target, opponent_tokens)
		if len(have_Target) != 0:
			have_Target.extend(self.limit_throw(opponent_tokens))
		# if no actions but have throws, just expand with throws
		elif self.remaining_throws != 0:
			have_Target = self.getThrowActions()
		# else no throw or no avaible action, just choose all move actions
		else:
			have_Target = actions
		have_Target = self.filter_action(have_Target)
		sorted_actions = self.sort_actions(have_Target, opponent_tokens)
		if len(sorted_actions) < max_actions:
			return sorted_actions 
		return sorted_actions[0:max_actions]
	
	def filter_action(self, actions):
		"""
		Filter out actions which eat token from the same team.
		"""
		no_collision = []
		for action in actions:
			collides = [x for x in self.team if x.position.distance(action.to_point) == 0]
			if not collides:
				no_collision.append(action)
		return no_collision
			

	def limit_throw(self, opponent_tokens):
		"""
		We want to limited the throw actions, so we set limit the number of each type throws.
		Also consider the current types on the board so the we want the token on the board be more diversity.
		"""

		# Limit throws to very specific scenarios
		# 1. Our tokens on the board are insufficient to win
		# 2. We can throw directly onto a target token and kill it when there are no nearby tokens that could kill it
		

		throws = self.getThrowActions()
		if len(throws) == 0:
			return []
		filtered_throws = []

		for throw in throws:
			distances = [throw.to_point.distance(token.position) for token in opponent_tokens if TARGETS[throw.tokenType] == token.tokenType]
			distances.append(MAX_DIS)
			if min(distances) == 0:
				filtered_throws.append(throw)

		flag = False
		ttypes = {ttype for ttype in Enums.TokenType}
		for opponent in opponent_tokens:
			if ENEMIES[opponent.tokenType] not in ttypes:
				continue
			for token in self.team:
				if TARGETS[token.tokenType] == opponent.tokenType:
					ttypes.remove(token.tokenType)
					break

		if len(ttypes) != 0:
			for ttype in ttypes:
				min_dist = MAX_DIS
				min_dist_throw = throws[0]
				for throw in throws:
					if throw.tokenType == ttype:
						distances = [throw.to_point.distance(token.position) for token in opponent_tokens if TARGETS[throw.tokenType] == token.tokenType]
						distances.append(MAX_DIS)
						if min(distances) < min_dist:
							min_dist = min(distances)
							min_dist_throw = throw

				filtered_throws.append(min_dist_throw)

		return filtered_throws



	def sort_actions(self, actions, opponent_tokens):
		"""
		Sort action list based on their distance to the closest opponent.
		actions: a list of actions
		opponent_tokens: all opponent tokens
		"""

		if not actions or not opponent_tokens:
			return actions
		ac_tup_list = []
		for action in actions:
			if not action:
				continue
			if isinstance(action, Action.ThrowAction):
				token_type = action.tokenType
			else:
				token_type = action.token.tokenType
			# got all distances to opponent
			distances = [action.to_point.distance(x.position) for x in opponent_tokens if TARGETS[token_type] == x.tokenType]
			if len(distances) == 0:
				#make the distance 10 since this is greater than the maximum distance. 
				dis = MAX_DIS
			else:
				dis = min(distances)
			if isinstance(action, Action.ThrowAction):
				dis = dis * 1.1

			ac_tup_list.append((action, dis))
		# sort ac_tup list based on its distance to opponent
		ac_tup_list = sorted(ac_tup_list, key=lambda x: x[1])
		return [action for (action, dis) in ac_tup_list]


	def getMoveActions(self):
		"""Generate all move actions of all tokens"""
		actions = []
		for token in self.team:
			actions.extend(token.getTokenActions(self.team))
		return actions
	


	def update(self, action):
		"""
		Update the team based on the received action.
		action: a tuple represents action
		"""
		if action[0] == "THROW":
			(_, tokenType, position) = action
			# position (r, q)
			#newToken = Token(position, self, tokenType)
			newToken = Token(position, self.teamtype, tokenType)
			self.add_to_team(newToken)
			self.remaining_throws -= 1

		# it is a slide or swing action
		else:
			(atype, (ra, qa), (rb, qb)) = action
			# get point from ra, qa and move to rb, qb
			original = self.gettoken(ra, qa)
			original.update(rb,qb)
		return
	
	def getThrowActions(self):
		"""
		Get possible valid throw actions for the team. The action list haven't sort by priority.
		!Since it generates all posible throws actions, which means we can further improve it by only generating most possible throw actions.!
		!Current don't eliminate the case when throws have collision with team member!
		:param tokens: all team tokens
		"""
		# return an empty list if we have already made 9 throws
		if self.remaining_throws == 0:
			return []

		actions = []
		# available throw region
		if self.teamtype == Enums.Team.UPPER:
			# count from the top row down
			# from_row < to_row
			to_row = BOARD_SIDE_LENGTH
			from_row = BOARD_SIDE_LENGTH - (INITIAL_THROW - self.remaining_throws)
						
		elif self.teamtype == Enums.Team.LOWER:
			from_row = -BOARD_SIDE_LENGTH
			to_row = -BOARD_SIDE_LENGTH + (INITIAL_THROW - self.remaining_throws)

		for row in range(from_row, to_row+1):
				for col in range(-BOARD_SIDE_LENGTH, BOARD_SIDE_LENGTH + 1):
					cell = Coordinate(row, col)
					if cell.isOnBoard():
						for tokenType in TOKEN_TYPE:
							actions.append(Action.ThrowAction(tokenType, cell))
		return actions



