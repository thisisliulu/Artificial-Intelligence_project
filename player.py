import luv.Enums as Enums
from luv.Board import Board
from luv.Coordinate import Coordinate
from luv.Strategy import *
from copy import deepcopy
import time
import random
# import json
# import os

# time limit is offset by one to account for the actual time taking 
# slightly more than what can be recorded by the player
TIME_LIMIT = 60
MAX_TURNS = 360
CONSTANT = 0.00000001

class Player:
    player: str
    def __init__(self, player):
        """
        Called once at the beginning of a game to initialise this player.
        Set up an internal representation of the game state.

        The parameter player is the string "upper" (if the instance will
        play as Upper), or the string "lower" (if the instance will play
        as Lower).
        
        """
        if player == "upper":
            self.team = Enums.Team.UPPER
        else:
            self.team = Enums.Team.LOWER
        
        # initiate the strategy
        self.board = Board(self.team, None)
        self.computation_time = 0
        self.turns = 0
        # self.record("luv/game_record.json", None, None)

    def action(self):
        """
        Called at the beginning of each turn. Based on the current state
        of the game, select an action to play this turn.
        """

        # constant that affects the rate of calculation time limit decrease
        RATE = 6
        MIN_CALC_TIME = 0.07

        # keep track of the players total number of turns
        self.turns += 1;

        # keep track of the players total computation time
        prior_t = time.time()
        newboard = deepcopy(self.board)

        if (self.computation_time == 0):
            # dont use monte carlo for the first move, just pick a move randomly
            strategy = Random(newboard)

        else:
            if (TIME_LIMIT - self.computation_time) / (MAX_TURNS - self.turns) <= MIN_CALC_TIME:
                calculation_time = (TIME_LIMIT - self.computation_time) / (MAX_TURNS - self.turns)
            calculation_time = RATE * ((TIME_LIMIT - self.computation_time) / (MAX_TURNS - self.turns))
            strategy = SM_MCTS(newboard, calculation_time)
        #MAX_DEPTH = 2
        #strategy = AlphaBeta_cutoff_MinMax(newboard, MAX_DEPTH)
        #strategy = Equilibrium_payoff(newboard)
        action = strategy.actions()
        self.computation_time += (time.time() - prior_t + CONSTANT)
        print("Total time:", self.computation_time, "\nTurns:", self.turns, "\n");

        # return the tuple representation of action
        return action.represent()
    
    def update(self, opponent_action, player_action):
        """
        Called at the end of each turn to inform this player of both
        players' chosen actions. Update your internal representation
        of the game state.
        The parameter opponent_action is the opponent's chosen action,
        and player_action is this instance's latest chosen action.
        """
        # put your code here
        # update players_action and opponent_action
        if self.team == Enums.Team.UPPER:
            self.board = self.board.update_board(player_action, opponent_action)
        else:
            self.board = self.board.update_board(opponent_action, player_action)
        # self.record("luv/game_record.json", opponent_action, player_action)

    # def record(self, file_path, opponent_action, player_action):
    # """
    # use for record each competition
    # """
    #     turn_records = "({},{}, {})".format(hash(self.board), opponent_action, player_action)
    #     if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
    #         with open(file_path, "w") as f:
    #             data = {str(id(self)): {str(self.turns): turn_records}}
    #             json.dump(data, f)
    #         return
        
    #     # game already starts and have actions
    #     with open(file_path, "r") as f:    
    #         previous = json.load(f)

        # if not opponent_action:
        #     data = {str(id(self)): {str(self.turns): turn_records}}
        #     previous.update(data)
        # else:
        #     previous[str(id(self))][str(self.turns)] = turn_records
        # with open(file_path, "w") as f:
        #     json.dump(previous,f)
        # return 

    # def rec_results(self, file_path, result, variables):
    #     if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
    #         with open(file_path, "w") as f:
    #             #data = {str(id(self)): {str(self.turns): turn_records}}
    #             data = {str(variabels): str(result)}
    #             json.dump(data, f)
    #         return
    #     if not opponent_action:
    #         data = {str(id(self)): {str(self.turns): turn_records}}
    #         previous.update(data)
    #     else:
    #         previous[str(id(self))][str(self.turns)] = turn_records
    #     with open(file_path, "w") as f:
    #         json.dump(previous,f)
    #     return 
