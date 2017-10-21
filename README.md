# AlphaGoBang - Implement AlphaZero in Gobang Game

MCTS and RL!



## CURRENT STAGE

Finish MCTS (hope so), with randomly choosen (p, v).

Speed test, single cpu: 13s / step (800 simulations with depth 40)


## SOME RESULTS

Now the MCTS search can find some foolish move (Just better than random)


Blue cells stand for black stones and purple for white. 

Yellow for higher MCTS enhanced policy (based on random prior) and green for 0.  



![avatar](./docs/foolish01.png)

![avatar](./docs/foolish02.png)


## Working

* Network.
* Each player play N board simultaneously, and share ONE TREE. THIS greatly speed up the generation of data.
* Multiple player. Unfortunately, tree cannot be reused.
