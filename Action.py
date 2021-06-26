import luv.Enums as Enums
BOARD_SIDE_LENGTH = 4

class Action:
    atype: str
    def __init__(self,atype):
        self.atype = atype

    def isVald(self):
        pass

    def __eq__(self, action):
        pass

class ThrowAction(Action):
    def __init__(self, tokenType, to_point):
        super().__init__(Enums.ActionType.THROW)
        self.tokenType = tokenType
        self.to_point = to_point

    # note that this isValid method does not check that the player has any remaining throws
    def isValid(self, remaining_throws, initial_throws, team):

        if team == Enums.Team.UPPER:
            valid_throw_row = self.to_point.x >= BOARD_SIDE_LENGTH - (initial_throws - remaining_throws)
        else:
            valid_throw_row = self.to_point.x <= -BOARD_SIDE_LENGTH + (initial_throws - remaining_throws)

        # add check that the throw is in a valid row
        return self.to_point.isOnBoard() and valid_throw_row
    def __eq__(self, other):
        if self.atype != other.atype:
            return False
        return self.tokenType == other.tokenType and self.to_point == other.to_point
    
    def represent(self):
        """
        Represent the action in the required format.
        """
        tokenType = 's'
        if self.tokenType == Enums.TokenType.R:
            tokenType = 'r'
        elif self.tokenType == Enums.TokenType.P:
            tokenType = 'p'
        return ("THROW", tokenType, self.to_point.toTuple())

    # for debugging purposes
    def toString(self):
        return "Action type: Throw, Token Type: " + str(self.tokenType) + ", Coordinates: " + self.to_point.toString()


class MoveAction(Action):
    def __init__(self, type, token, to_point):
      super().__init__(type)
      self.to_point = to_point
      self.token = token

    def __eq__(self, other):
        if self.atype != other.atype:
            return False
        return self.token == other.token and self.to_point == other.to_point

    def isValid(self):
        return self.to_point.isOnBoard()
        
    # for debugging purposes
    def toString(self):
        return "Action type: " + str(self.token.tokenType) + ", From: " + self.token.position.toString() + ", To: " + self.to_point.toString()



class SlideAction(MoveAction):
    #def __init__(self,token, from_point, to_point):
    #  super().__init__(Enums.ActionType.SLIDE, token, from_point, to_point)
    def __init__(self, token, to_point):
        super().__init__(Enums.ActionType.SLIDE, token, to_point)
    
    def isValid(self):
        # only checks that the slide to position is on the board
        return super().isValid()

    def represent(self):
        return ("SLIDE", self.token.position.toTuple(), self.to_point.toTuple())


class SwingAction(MoveAction):

    def __init__(self,token, to_point):
        super().__init__(Enums.ActionType.SWING, token, to_point)
    
    def isValid(self):
        # only checks that the swing to position is on the board
        return super().isValid()
        
    def represent(self):
        return ("SWING", self.token.position.toTuple(), self.to_point.toTuple())



      
      