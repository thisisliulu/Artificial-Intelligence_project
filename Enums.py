from enum import Enum

class Team(Enum):
	UPPER = "upper"
	LOWER = "lower"

class TokenType(Enum):
	R = 'r'
	P = 'p'
	S = 's'

class ActionType(Enum):
	THROW = "THROW"
	SLIDE = "SLIDE"
	SWING = "SWING"
