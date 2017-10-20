# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: mcts_template.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017

#!/usr/bin/env python
import random
import math
import hashlib
import logging
import argparse
"""
A quick Monte Carlo Tree Search implementation.  For more details on MCTS see See http://pubs.doc.ic.ac.uk/survey-mcts-methods/survey-mcts-methods.pdf
The State is just a game where you have NUM_TURNS and at turn i you can make
a choice from [-2,2,3,-3]*i and this to to an accumulated value.  The goal is for the accumulated value to be as close to 0 as possible.
The game is not very interesting but it allows one to study MCTS which is.  Some features
of the example by design are that moves do not commute and early mistakes are more costly.
In particular there are two models of best child that one can use
"""

#MCTS scalar.  Larger scalar will increase exploitation, smaller will increase exploration.
SCALAR = 1 / math.sqrt(2.0)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('MyLogger')


class State():
    NUM_TURNS = 10
    GOAL = 0
    MOVES = [2, -2, 3, -3]
    MAX_VALUE = (5.0 * (NUM_TURNS - 1) * NUM_TURNS) / 2
    num_moves = len(MOVES)

    def __init__(self, value=0, moves=[], turn=NUM_TURNS):
        self.value = value
        self.turn = turn
        self.moves = moves

    def next_state(self):
        nextmove = random.choice([x * self.turn for x in self.MOVES])
        next = State(self.value + nextmove, self.moves + [nextmove],
                     self.turn - 1)
        return next

    def terminal(self):
        if self.turn == 0:
            return True
        return False

    def reward(self):
        r = 1.0 - (abs(self.value - self.GOAL) / self.MAX_VALUE)
        return r

    def __hash__(self):
        return int(hashlib.md5(str(self.moves)).hexdigest(), 16)

    def __eq__(self, other):
        if hash(self) == hash(other):
            return True
        return False

    def __repr__(self):
        s = "Value: %d; Moves: %s" % (self.value, self.moves)
        return s


class Node():
    def __init__(self, state, parent=None):
        self.visits = 1
        self.reward = 0.0
        self.state = state
        self.children = []
        self.parent = parent

    def add_child(self, child_state):
        child = Node(child_state, self)
        self.children.append(child)

    def update(self, reward):
        self.reward += reward
        self.visits += 1

    def fully_expanded(self):
        if len(self.children) == self.state.num_moves:
            return True
        return False

    def __repr__(self):
        s = "Node; children: %d; visits: %d; reward: %f" % (len(self.children),
                                                            self.visits,
                                                            self.reward)
        return s


def UCTSEARCH(budget, root):
    for iter in range(budget):
        if iter % 10000 == 9999:
            logger.info("simulation: %d" % iter)
            logger.info(root)
        front = TREEPOLICY(root)
        reward = DEFAULTPOLICY(front.state)
        BACKUP(front, reward)
    return BESTCHILD(root, 0)


def TREEPOLICY(node):
    while node.state.terminal() == False:
        if node.fully_expanded() == False:
            return EXPAND(node)
        else:
            node = BESTCHILD(node, SCALAR)
    return node


def EXPAND(node):
    tried_children = [c.state for c in node.children]
    new_state = node.state.next_state()
    while new_state in tried_children:
        new_state = node.state.next_state()
    node.add_child(new_state)
    return node.children[-1]


#current this uses the most vanilla MCTS formula it is worth experimenting with THRESHOLD ASCENT (TAGS)
def BESTCHILD(node, scalar):
    bestscore = 0.0
    bestchildren = []
    for c in node.children:
        exploit = c.reward / c.visits
        explore = math.sqrt(math.log(2 * node.visits) / float(c.visits))
        score = exploit + scalar * explore
        if score == bestscore:
            bestchildren.append(c)
        if score > bestscore:
            bestchildren = [c]
            bestscore = score
    if len(bestchildren) == 0:
        logger.warn("OOPS: no best child found, probably fatal")
    return random.choice(bestchildren)


def DEFAULTPOLICY(state):
    while state.terminal() == False:
        state = state.next_state()
    return state.reward()


def BACKUP(node, reward):
    while node != None:
        node.visits += 1
        node.reward += reward
        node = node.parent
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MCTS research code')
    parser.add_argument('--num_sims', action="store", required=True, type=int)
    parser.add_argument(
        '--levels',
        action="store",
        required=True,
        type=int,
        choices=range(State.NUM_TURNS))
    args = parser.parse_args()

    current_node = Node(State())
    for l in range(args.levels):
        current_node = UCTSEARCH(args.num_sims / (l + 1), current_node)
        print("level %d" % l)
        print("Num Children: %d" % len(current_node.children))
        for i, c in enumerate(current_node.children):
            print(i, c)
        print("Best Child: %s" % current_node.state)

        print("--------------------------------")
