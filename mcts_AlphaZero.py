import chess
import numpy as np
import copy

# from pettingzoo.classic import chess_v6
# from pettingzoo.classic.chess import chess_utils as ut


def softmax(x):
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs

# def label_moves(df):
#     df['player'] = [(8 if i % 2 == 0 else 9) for i in range(len(df))]
#     return df
#
#
# def move_map_black(move):
#     TOTAL = 73
#     source = move.from_square
#     coord = ut.square_to_coord(source)
#     panel = ut.get_move_plane(move)
#     cur_action = (coord[0] * 8 + coord[1]) * TOTAL + panel
#     return cur_action


# def move_map_white(uci_move):
#     TOTAL = 73
#     move = chess.Move.from_uci(uci_move)
#     source = move.from_square
#     coord = ut.square_to_coord(source)
#     panel = ut.get_move_plane(move)
#     cur_action = (coord[0] * 8 + coord[1]) * TOTAL + panel
#     return cur_action
#
#
# def black_move(uci_move):
#     move = chess.Move.from_uci(uci_move)
#     mir = ut.mirror_move(move)
#     return mir


class TreeNode(object):
    """A node in the MCTS tree.

    Each node keeps track of its own value Q, prior probability P, and
    its visit-count-adjusted prior score u.
    """

    def __init__(self, parent, prior_p):
        self._parent = parent
        self._children = {}  # a map from action to TreeNode
        self._n_visits = 0
        self._Q = 0
        self._u = 0
        self._P = prior_p

    def expand(self, action_priors):
        """Expand tree by creating new children.
        action_priors: a list of tuples of actions and their prior probability
            according to the policy function.
        """
        for action, prob in action_priors:
            if action not in self._children:
                self._children[action] = TreeNode(self, prob)

    def select(self, c_puct):
        """Select action among children that gives maximum action value Q
        plus bonus u(P).
        Return: A tuple of (action, next_node)
        """
        return max(self._children.items(),
                   key=lambda act_node: act_node[1].get_value(c_puct))

    def update(self, leaf_value):
        """Update node values from leaf evaluation.
        leaf_value: the value of subtree evaluation from the current player's
            perspective.
        """
        # Count visit.
        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        self._Q += 1.0*(leaf_value - self._Q) / self._n_visits

    def update_recursive(self, leaf_value):
        """Like a call to update(), but applied recursively for all ancestors.
        """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.update_recursive(-leaf_value)
        self.update(leaf_value)

    def get_value(self, c_puct):
        """Calculate and return the value for this node.
        It is a combination of leaf evaluations Q, and this node's prior
        adjusted for its visit count, u.
        c_puct: a number in (0, inf) controlling the relative impact of
            value Q, and prior probability P, on this node's score.
        """
        self._u = (c_puct * self._P *
                   np.sqrt(self._parent._n_visits) / (1 + self._n_visits))
        return self._Q + self._u

    def is_leaf(self):
        """Check if leaf node (i.e. no nodes below this have been expanded)."""
        return self._children == {}

    def is_root(self):
        return self._parent is None


class MCTS(object):
    """An implementation of Monte Carlo Tree Search."""

    def __init__(self, policy_value_fn, c_puct=5, n_playout=10000):
        """
        policy_value_fn: a function that takes in a board state and outputs
            a list of (action, probability) tuples and also a score in [-1, 1]
            (i.e. the expected value of the end game score from the current
            player's perspective) for the current player.
        c_puct: a number in (0, inf) that controls how quickly exploration
            converges to the maximum-value policy. A higher value means
            relying on the prior more.
        """
        self._root = TreeNode(None, 1.0)
        self._policy = policy_value_fn
        self._c_puct = c_puct
        self._n_playout = n_playout

    def _playout(self, env, state):
        """Run a single playout from the root to the leaf, getting a value at
        the leaf and propagating it back through its parents.
        State is modified in-place, so a copy must be provided.
        """
        node = self._root
        # observation, reward, termination, truncation, info = env.last()

        while(1):
            if node.is_leaf():
                break
            # Greedily select next move.
            action, node = node.select(self._c_puct)
            env.step(action)

        available, action_probs, leaf_value = self._policy(env, state)
        action_probs = zip(available, action_probs[available])
        # observation, reward, termination, truncation, info = env.last()

        if env.terminal is not True:
            node.expand(action_probs)

        else:
            # reward = env.reward
            if env.reward == 0:  # tie
                leaf_value = 0.0
            elif env.reward == env.turn:
                leaf_value = 1.0
            else:
                leaf_value = -1.0

        # Update value and visit count of nodes in this traversal.
        node.update_recursive(-leaf_value)

    def get_move_probs(self, env, state, temp=1e-3):
        """Run all playouts sequentially and return the available actions and
        their corresponding probabilities.
        state: the current game state
        temp: temperature parameter in (0, 1] controls the level of exploration
        """
        for n in range(self._n_playout):
            # env_new = chess_v6.env()
            # env_new.reset()
            # for move in move_list:
            #     env.step(move)
            # env_copy.agent_selection = env.agent_selection
            state_copy = copy.deepcopy(state)
            env_copy = copy.deepcopy(env)

            self._playout(env_copy, state_copy)

        # calc the move probabilities based on visit counts at the root node
        act_visits = [(act, node._n_visits)
                      for act, node in self._root._children.items()]
        acts, visits = zip(*act_visits)
        act_probs = softmax(1.0/temp * np.log(np.array(visits) + 1e-10))

        return acts, act_probs

    def update_with_move(self, last_move):
        """Step forward in the tree, keeping everything we already know
        about the subtree.
        """
        if last_move in self._root._children:
            self._root = self._root._children[last_move]
            self._root._parent = None
        else:
            self._root = TreeNode(None, 1.0)

    def __str__(self):
        return "MCTS"


class MCTSPlayer(object):
    """AI player based on MCTS"""

    def __init__(self, policy_value_function,
                 c_puct=5, n_playout=2000, is_selfplay=0):
        self.mcts = MCTS(policy_value_function, c_puct, n_playout)
        self._is_selfplay = is_selfplay

    def set_player_ind(self, p):
        self.player = p

    def reset_player(self):
        self.mcts.update_with_move(-1)

    def get_action(self, env, obs, temp=1e-3, return_prob=0):
        # legal_moves = []
        # uci_moves = list(env.env.env.env.board.legal_moves)
        # uci_moves = [move.uci() for move in uci_moves]
        # if env.env.env.env.board.turn == True:
        #     for uci_move in uci_moves:
        #         legal_moves.append(move_map_white(uci_move))
        # else:
        #     for uci_move in uci_moves:
        #         move = black_move(uci_move)
        #         legal_moves.append(move_map_black(move))

        move_probs = np.zeros(obs.shape[0] * obs.shape[1] * 73)

        if env.terminal is not True:
            # acts, probs = self.mcts.get_move_probs(move_list, temp)
            acts, probs = self.mcts.get_move_probs(env, obs, temp)
            move_probs[list(acts)] = probs
            if self._is_selfplay:
                # add Dirichlet Noise for exploration (needed for self-play training)
                move = np.random.choice(
                    acts,
                    p=0.75*probs + 0.25*np.random.dirichlet(0.3*np.ones(len(probs)))
                )
                # update the root node and reuse the search tree
                self.mcts.update_with_move(move)
            else:
                # with the default temp=1e-3, it is almost equivalent to choosing the move with the highest prob
                move = np.random.choice(acts, p=probs)
                # reset the root node
                self.mcts.update_with_move(-1)

            if return_prob:
                return move, move_probs
            else:
                return move
        else:
            print("WARNING: the board is full")

    def __str__(self):
        return "MCTS {}".format(self.player)