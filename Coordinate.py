import luv.Enums as Enums

BOARD_SIDE_LENGTH = 4

class Coordinate:
	x: int
	y: int
	def __init__(self, x, y):
		self.x = x
		self.y = y

	# def copy(self):
	# 	return Coordinate(self.x, self.y)
		
	def __eq__(self,other):
		return self.x == other.x and self.y == other.y

	def distance(self, other):
		"""
		Reused code from part A
		Return the number of steps between two points (manhattan distance on hexagonal grids)
		https://stackoverflow.com/questions/5084801/manhattan-distance-between-tiles-in-a-hexagonal-grid/5085274#5085274
		"""
		#x_a, y_a = point_a
		#x_b, y_b = point_b
		#dx = x_a - x_b
		#dy = y_a - y_b

		dx = self.x - other.x
		dy = self.y - other.y


		# since don't have sign() in python, so if dx and dy is the same sign, then the multiply will be >0
		if dx * dy > 0:
		    return abs(dx + dy)
		else:
		    return max(abs(dx), abs(dy))

	def isOnBoard(self):
		"""
		Returns true if the coordinate identifies a position on the hexagonal grid and false otherwise
		"""
		# the board dimension is the number of hexes along each side of the board offset by 1
		xValid = self.x <= BOARD_SIDE_LENGTH and self.x >= -BOARD_SIDE_LENGTH
		yValid = self.y <= BOARD_SIDE_LENGTH and self.y >= -BOARD_SIDE_LENGTH
		sumValid = self.x + self.y <= BOARD_SIDE_LENGTH and self.x + self.y >= -BOARD_SIDE_LENGTH
		return xValid and yValid and sumValid

	def toTuple(self):
		return (self.x, self.y)
	# for debugging purposes
	def toString(self):
		return "(" + str(self.x) + ", " + str(self.y) + ")"

