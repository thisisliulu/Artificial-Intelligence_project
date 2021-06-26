from luv.Board import Board
import luv.Enums as Enums
from luv.Action import Action
from luv.gametheory import solve_game
from collections import defaultdict
import numpy as np
import time
import random
from copy import deepcopy
import sys
sys.setrecursionlimit(10000)
WIN = 1
LOSE = -1
DRAW = 0
ALL_SYMBOLS = ['r', 'p', 's']
EXPLORATION = 1/np.sqrt(2)
EXPLOITATION = 0

class Strategy:
    board: Board

    def __init__(self, board):
        self.board = board
        self.history = defaultdict(int)
        self.history[hash(board)] += 1

    def actions(self):
        pass
    
    def goal_test(self, board):
        """
        The general goal test for all stratygies.
        """
        if self.history[hash(board)] >= 3:
            board.utility = DRAW
            return True
        return board.goal_test()
    
class Random(Strategy):
    """
    Strategy to get a random action.
    """
    def __init__(self, board):
        super().__init__(board)

    def actions(self):
        # random is very fast so we can consider as many actions as we want
        action_limit = 1000
        actions = self.board.getActions(self.board.team, action_limit)
        index = random.randint(0, len(actions)-1)
        action = actions[index]
        return action


class AlphaBeta_cutoff_MinMax(Strategy):
    """
    board: board when strategy starts
    d: cut-off depth
    """
    def __init__(self, board, d):
        super().__init__(board)
        self.d = d 

    def evaluation(self):
        """
        Calculate the evaluation score
        """
        # feature 1: throw difference
        upper = self.board.uppers
        lower = self.board.lowers
        diff_throw = upper.remaining_throws - lower.remaining_throws
        # feature2: different token numbers
        upper_group = upper.group_team()
        lower_group = lower.group_team()
        diff_token = np.sum([len(upper_group[a])- len(lower_group[a]) for a in ALL_SYMBOLS])
        self.board.utility = 0.7 * diff_token + 0.3 * diff_throw
        return self.board.utility

    def cutoff_test(self, board):
        if self.goal_test(board) or board.depth > self.d + self.board.depth:
            board.utility = self.evaluation()
            return True
        return False

    def min_val(self, board, alpha, beta):
            """
            When the player is LOWER side.
            Reference : https://github.com/aimacode/aima-python/blob/master/games.py
            """
            if self.cutoff_test(board) and board.utility:
                return -board.utility
            
            v = np.inf
            for a in board.getActions(Enums.Team.LOWER, 10):
                v = min(v, self.max_val(board.result(a, Enums.Team.LOWER), alpha, beta))
                if v <= alpha:
                    return v
                beta = min(beta, v)
            return v
        
    def max_val(self, board, alpha, beta):
            """
            When the player is UPPER side.
            code reference : https://github.com/aimacode/aima-python/blob/master/games.py
            """
            if self.cutoff_test(board):
                return board.utility
            v = -np.inf
            for a in board.getActions(Enums.Team.UPPER, 10):
                v = max(v, self.min_val(board.result(a, Enums.Team.UPPER), alpha, beta))
                if v >= beta:
                    return v
                alpha = max(v, alpha)
            return v
        
    def actions(self):
        """
        Use minmax strategy to calculate the best move by searching
        forward all the way to the terminal states.
        :param board: current board
        """
        # our team should decide which action to take
        board = self.board
        player = self.board.team
        # alpha is the best for Upper along the path to state
        alpha = -np.inf

        # beta is the best for lower along the path to state
        beta = np.inf
        
        best_action = None
        NUM_ACTIONS = 5
        if player == Enums.Team.UPPER:
            for a in board.getActions(player, NUM_ACTIONS):
                v = self.min_val(board.result(a, Enums.Team.UPPER), alpha, beta)
                if v > alpha:
                    alpha = v
                    best_action = a
            return best_action
        
        if player == Enums.Team.LOWER:
            for b in board.getActions(player, NUM_ACTIONS):
                v = self.max_val(board.result(b, Enums.Team.LOWER), alpha, beta)
                if v < beta:
                    beta = v
                    best_action = b
            return best_action
  
class Equilibrium_payoff(Strategy):
    """
    Level 1: based on 1 more level payoff matrix and find out Nash equilibrium.
    Then use random sample to get action.
    """
    def __init__(self, board):
        super().__init__(board)

    def compute_payoff_matrix(self, board, upper_actions, lower_actions):
        """
        Return the payoff matrix (upper as row and lower as column)
        Payoff value is the evaluation value of upper.
        """
        payoff = []
        for upper_ac in upper_actions:
            payoff_row = []
            for lower_ac in lower_actions:
                newboard = board.update_board(upper_ac.represent(), lower_ac.represent())
                payoff_row.append(newboard.evaluation_score())
            payoff.append(payoff_row)
        return payoff

    def actions(self):
        # Note: action limit should change as we get further into the game / further into the search
        # For now, action limit behaves like a constant. 
        action_limit = 15
        upper_actions = self.board.getActions(Enums.Team.UPPER, action_limit)
        lower_actions = self.board.getActions(Enums.Team.LOWER, action_limit)
        payoff_matrix = self.compute_payoff_matrix(self.board, upper_actions, lower_actions)
        if self.board.team == Enums.Team.UPPER:
            s, v = solve_game(payoff_matrix, True, True)
            action = np.random.choice(upper_actions, 1,  p= s)[0]
            return action
        else:
            s,v  = solve_game(payoff_matrix, False, False)
            action = np.random.choice(lower_actions, 1, p = s)[0]
            return action


class SM_MCTS(Strategy):
    """
    Simultaneous-move game use Monte Carlo Tree Search.
    logic: Selection, Expansion, Simulation, Bachpropagation
    source: 
    1 .https://www.researchgate.net/publication/235985858_A_Survey_of_Monte_Carlo_Tree_Search_Methods 
    Page 9, Algorithm 2, the UCT algorithm
    2. https://www.geeksforgeeks.org/ml-monte-carlo-tree-search-mcts/

    """
    def __init__(self, board, calculation_time):
        super().__init__(board)
        # restrict calculation time
        self.calculation_time = calculation_time
        # a dictionary to record the visit and wins count
        self.visit = defaultdict(int)
        self.wins = defaultdict(int)

    def ucb(self, childboard, exploitation):
        """
        UCB formula (Upper confidence bound) is based on 
        https://www.researchgate.net/publication/235985858_A_Survey_of_Monte_Carlo_Tree_Search_Methods
        Page 5, section 2.4.2
        UCB formula: Wi/Ni + C * sqrt(2ln(N)/ Ni) 
        Wi: win count for child node
        Ni: visit count for child node
        N: visit count for parent node
        C: exploration parameter
        Wi/Ni: exploitation part
        sqrt(2ln(N)/ Ni): exploration part∂
        from the source, "the term 'sqrt(2ln(N)/ Ni)' encourage the exploration of less visited nodes"
            if exploration, use EXPLORATION = 1/np.sqrt(2)
            otherwise just use the exploitation part to find best child
        param:
        board: childboard

        """
        if self.visit[childboard] == 0:
            return np.inf
        if exploitation == True:
            confidence = EXPLOITATION
        else:
            confidence = EXPLORATION
        return self.wins[childboard]/self.visit[childboard] + confidence * np.sqrt(2*np.log(self.visit[childboard.parent])/self.visit[childboard])
    
    def actions(self):
        """
        Main part for the Monte Carlo Tree Search, 
        """
        begin_time = time.time()
        while time.time() - begin_time < self.calculation_time:
            leaf = self.selection(self.board)
            simulation_result = self.simulation(leaf)
            self.backpropagate(leaf, simulation_result)
        # print(time.time()- begin_time)
        best_child = self.best_child(self.board, True)
        if self.board.team == Enums.Team.UPPER:
            # since the board child is in the form of (child board: (upper_action, lower_action))
            # so best child will give the combination of actions (upper_action, lower_action)
            # if our side is upper, use index 0
            return self.board.child[best_child][0]
        else:
            # if our side in lower, use index 1 
            return self.board.child[best_child][1]
    
    def selection(self, board):
        """
        If the node is not the terminal,
        ---- if not fully expand, expand 
        ---- if expands fully, return the best child (use UCB)
        """
        node = board
        while not self.goal_test(node):
            if node.isFullyExpand == False:
                return self.expansion(node)
            else:
                node = self.best_child(node, False)
        return node

    def expansion(self,board):
        """
        Expand one childboard for the current board each time.
        """
        tries_action = board.child.values()
        NUM_ACTIONS = 10
        # generate actions
        lower_actions = board.getActions(Enums.Team.LOWER, NUM_ACTIONS)
        upper_actions = board.getActions(Enums.Team.UPPER, NUM_ACTIONS)
        
        # combination of actions
        comb = list(zip(upper_actions, lower_actions))
        remaining = [x for x in comb if x not in tries_action]

        if len(remaining) == 1:
            action = remaining[0]
            board.isFullyExpand = True
        elif len(remaining) > 1:
            # action in the form (upper_ac, lower_ac)
            action = remaining[random.randint(0, len(remaining) - 1)]
        else:
            action = comb[random.randint(0, len(comb) - 1)]
        childboard = board.update_board(action[0].represent(), action[1].represent())
        board.child[childboard] = action
        # visit dictionary records how many time we visit the child board during simulation
        self.visit[childboard] = 0

        # wins dictionary records during simulation how many times we win
        self.wins[childboard] = 0
        return childboard
    
    def simulation(self, board):
        """
        Simulation part. Randomly rollout.
        """
        node = board
        NUM_ACTIONS = 5
        while True:
            if self.goal_test(node):
                if node.team == Enums.Team.UPPER:
                    return node.utility
                return -node.utility
            lower_actions = node.getActions(Enums.Team.LOWER, NUM_ACTIONS)
            upper_actions = node.getActions(Enums.Team.UPPER, NUM_ACTIONS)
            # combination of actions
            comb = list(zip(upper_actions, lower_actions))

            # get random rollout
            action = comb[random.randint(0, len(comb) - 1)]

            node = node.update_board(action[0].represent(), action[1].represent())
        return 

    def best_child(self, board, confidence):
        """
        Sort board child based on their ucb value.
        board: the parent board to find the best child
        confidence: if True, then the calculation of ucb focuses on exploration, otherwise focusing on exploitation.
        """
        best_value = -np.inf
        best_child = []

        for childboard, action in board.child.items():
            ucb = self.ucb(childboard, confidence)
            if ucb > best_value:
                best_value = ucb
                best_child = [childboard]
            if ucb == best_value:
                best_child.append(childboard)
                
        # in case of no best child, return the best action
        if not best_child:
            if board.team == Enums.Team.UPPER:
                return board.uppers.getLimitedActions(board.lowers.team, 1)
            else:
                return board.lowers.getLimitedActions(board.uppers.team, 1)
        # if there is many best child, return the first 1
        # otherwise, return the only child in best_child
        return  best_child[0]
    
    def backpropagate(self, board, result):
        """
        After each simulation, propagate the visit and win's result back to root.
        board: the leaf node which has a result
        result: win/lose/draw
        """
        node = board
        while not node:
            self.visit[node] += 1
            if result == WIN:
                self.wins[node] += 1
            else:
                # wanna penalise the move if results in draw or lose
                self.wins[node] -= 1
            node = node.parent
        return 
    

            


        


        

    

        