from ai.mcts_policy import Tree, plot_pi, legal, move_state
from env.gobang import Game, axis, toind
tree = Tree()
g = Game()
g.add(7, 7)
g.add(3, 7)
g.add(7, 8)
g.add(3, 8)
g.add(7, 5)
g.add(1, 7)
g.add(10, 8)
g.add(2, 8)
g.add(7, 6)
g.add(10, 10)
pi = tree.get_pi(10, g.black, g.white)
plot_pi(g.black, g.white, pi)

tree = Tree()
g = Game()
g.add(7, 7)
g.add(3, 7)
g.add(7, 8)
g.add(3, 8)
g.add(10, 8)
g.add(2, 8)
g.add(7, 6)
g.add(10, 10)
pi = tree.get_pi(10, g.black, g.white)
plot_pi(g.black, g.white, pi)

tree = Tree()
g = Game()
g.add(7, 7)
g.add(3, 7)
g.add(7, 6)
g.add(3, 8)
g.add(8, 6)
g.add(1, 7)
g.add(7, 8)
g.add(2, 8)
g.add(9, 7)
g.add(10, 10)
pi = tree.get_pi(10, g.black, g.white)
plot_pi(g.black, g.white, pi)