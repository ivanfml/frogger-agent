# frogger-agent

## Software/Hardware Requirments

- macOS (tested on Mac Tahoe) or Linux
- Tested on Python 3.14.2
- Homebrew (for MacOS 10 or higher) https://brew.sh

### Installation Process for MacOS 10 or higher
1. Run `brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf pkg-config`
2. Create and activate virtual environment:
    - `python -m venv .venv` 
    - `source venv/bin/activate`
3. Run `pip install pygame`

To verify installation, you can run `python -m pygame.examples.aliens`, if the game shows up and you can play it, then installation was done properly.

For more details on pygame installation, you can go to https://www.pygame.org/wiki/MacCompile. For more general details on pygame installion, you can go to https://www.pygame.org/wiki/GettingStarted.

## Running Frogger
- Run `python frogger.py` to play regular (user as player) frogger. (The game code base is from https://github.com/jgubert/frogger and `frogger.py` is the only file that we did not write)
- Run `python frogger_agent.py` for the automated agent to play frogger (`frogger_agent.py` is just a copy of `frogger.py` but with the agent's decision integration)

## Problem Statement

For this project, we want to build an agent that can play the Frogger game (using the PyGame version, pyFrogger) on its own. The goal of the agent is to move the frog from the starting position to the goal area while avoiding obstacles like cars and water. At each step, the agent has to decide what move to make (up, down, left, right, or stay), based on what’s currently happening in the game. Since the game progresses over time and the agent keeps making decisions step by step, this fits as a sequential decision-making problem. 


## Related Solutions to Similar Problems

https://www.cs.swarthmore.edu/~meeden/cs81/s14/papers/DavisJake.pdf
This report written by two Swarthmore college students contains the strongest existing solution method to implement an agent to solve Frogger at maximum or close to maximum efficiency that I could find. The students implemented a NEAT-based solution (genetic algorithm called NeuroEvolution of Augmenting Topologies) to solve Frogger. To briefly summarize their solution, they first set out to make their frog able to learn how to avoid colliding with obstacles in traffic, while also staying on logs in the river section of their version of Frogger. To account for this, they equipped their frog with 11 sensors and also one extra sensor dedicated to sensing the position of the frog in the world. 

In addition to those basic details, they tested their Frog with experiments using a fitness function that exponentially rewarded their frog for moving closer to the goal zone.

As for the NEAT algorithm, they used it to evolve the weights of the connections and the topology of the neural networks that controlled their frog. They found that NEAT was able to consistently find optimal solutions in all of their Frogger variations in under 100 generations.

In this case, the Swarthmore report falls under Reinforcement Learning.
The fitness function that rewards the frog based on its behavior was the strongest indicator to me that this solution method could be generalized under Reinforcement Learning.

## Motivation

Our inspiration for choosing to create an agent to solve Frogger comes from the game's renown in the gaming industry and the interest in the algorithm we used to solve it, MCTS. 

Frogger is not only a game we enjoy playing, but it is also well known as a classic of the Golden Age of Arcade Games. Due to its popularity, most know at least the rules and the objective of the game. Thus, making the game itself easy to understand and for the average person to notice whether or not the agent works properly.

Also, MCTS is an algorithm that was well discussed in class and one that we found very interesting simply because how it works through its logic in order to get the best possible action. Because of this and becuase we believed it could work as a good and challenging solution to the problem, we gave it much weight on our final decision to pick this project topic. (More on MCTS in the "Our Solution" section)

## State Space Specification

### Mathematical description of States, Transitions, Actions and Rewards
 
A **state** $s \in S$ is a tuple:
 
$$
s = (p, C, L, g, f, \text{speed}, \text{level}, t, \tau, T_C, T_L)
$$

where: 
- $p = (x_f, y_f) \in \mathbb{Z}^2$ — frog pixel position, with $x_f \in [2, 401]$ and $y_f \in [39, 475]$
- $C = \\{(x_i^c,\ y_i^c,\ d_i^c,\ k_i)\\}$ — for $i=1, 2, \cdots, n_c$ active cars, where $x_i^c$ is x position, $y_i^c \in \\{280, 318, 357, 397, 436\\}$ is the lane, $d_i^c \in \\{\text{left}, \text{right}\\}$ is direction, and $k_i \in \\{1, 2\\}$ is the speed factor
- $L = \\{(x_j^l,\ y_j^l,\ d_j^l)\\}$ — for $j=1,\cdots,n_l$ active logs, where $y_j^l \in \\{44, 83, 122, 161, 200\\}$
- $g \in \\{0,1,2,3,4,5\\}$ — number of goal slots currently filled
- f ⊆ {0,1,2,3,4} — set of indices of lily pads already filled in the current level
- $\text{speed} \in \mathbb{Z}^+$ — current game speed (starts at 3, increments each level)
- $\text{level} \in \mathbb{Z}^+$ — current level number
- $t \in \\{0, \ldots, 30\\}$ — seconds remaining in the current life
- $\tau \in \\{0, \ldots, 30\\}$ — tick countdown within the current second (when $\tau$ hits 0, $t$ decrements by 1)
- $T_C \in \mathbb{R}^5$ — per-lane spawn countdown timers for cars (one per lane)
- $T_L \in \mathbb{R}^5$ — per-lane spawn countdown timers for logs (one per lane)
 
**Actions:** At each tick the agent picks one of:
 
$$A = \\{\text{up},\ \text{down},\ \text{left},\ \text{right},\ \text{stay}\\}$$
 
Up/down actions move $y_f$ by $\pm 39\text{px}$ per agent decision. Left/right actions move $x_f$ by $\pm 41\text{px}$ per agent decision.
 
**Transitions:** $T(s, a) \to s'$:
 
Deterministic part (every tick):
- Each car moves: $x_i^c += \text{speed} \cdot k_i$ if going right or $x_i^c -= \text{speed} \cdot k_i$ if going left. Cars outside bounds are removed.
- Each log moves: $x_j^l += \text{speed}$ if going right or $x_j^l -= \text{speed}$ if going left. Logs outside bounds are removed.
- Each timer in $T_C$ and $T_L$ decrements by 1. When a timer hits 0, a new car or log is spawned in that lane and the timer resets to $(\text{base} \cdot \text{speed}) / \text{level}$, where base varies per lane.
- If the frog is in the river zone and on a log, $x_f$ drifts by $\pm \text{speed}$ each tick regardless of the action taken.
- The frog's position updates according to $a$.
- $\tau' = \tau - 1$. When $\tau' = 0$, $t' = t - 1$ and $\tau'$ resets to 30. If $t' = 0$ the frog loses a life and resets.
 
Stochastic part (~4% chance per tick):
- One car is chosen at random and it moves to a different lane by ±39px in y, bounded to $y \in [280, 436]$. 

So, the state that the agent transition to depends on whether or not ~4% chance hit or not.
 
## Our Solution

Our algorithmic solution to Frogger is Monte Carlo Tree Search (MCTS). The basics of how it works is that it builds a search tree by sampling future moves. Each node represents a Frogger state and the edges are the actions leading to the next possible states. So, starting from the root node, MCTS explores action sequences and estimates best outcomes. We based our version of MCTS on Mykel Kochenderfer's (Decision Making Under Uncertainty, MIT Press 2015) version. Like Kochenderfer, we used UCB1 as our exploration heuristic, with our exploration constant set to 5.0, which is higher than the textbook value of $\sqrt{2}$ because we found that lower values caused the agent to lock in early Q estimates and stop exploring alternative actions.

We implemented a greedy rollout policy. At each step of the rollout, instead of picking an action at random, we check all possible actions and using the potential function on the resulting state in order to pick whichever action scores highest. If any action would cost the frog a life, we add a penalty of $-2000$ to its score and if any action reaches a goal slot we add a "goal reward" currently set to $5000$. This gives MCTS a better rollout to work with rather than random actions, since taking random actions in Frogger almost always ends in death within a few steps. Thus, our rollout policy helps MTCS build a more appropriate and accurate tree for decision making.

The reward at each step is computed using our potential function. Rather than only giving reward at terminal events (goal reached and death), we define a potential function that scores how good any given state is, and the step reward is the difference in potential between the current and next state plus any terminal reward. This means the agent gets a more informed reward at every step rather than just waiting until something critical happens.

The potential function itself combines several parts in order to get a better agent. The part that we gave most weight is progress toward the goal, which we scored based on how far up the screen the frog has moved (the more the better). Also, the function penalizes car danger in the road zone by looking at whether any car's predicted future lane is the same as the frog's lane. In the river zone it penalizes being off a log, and when on a log it adds a smaller penalty based on how close the frog is to drifting off the edge. Finally, when the frog is near the goal zone, the function rewards being horizontally aligned with a goal slot that has not been used yet and penalizes being near goal spot that has already been filled previously in the level.

## Measuring Success

Measuring success in a Frogger-playing agent wasn't as straightforward as a single accuracy number, because the agent has to consider multiple competing objectives: surviving, making progress, avoiding obstacles, and ultimately filling all five lily pads at each level. We evaluated the agent along three aspects, each an important aspect of "good play".

### 1. Survival rate

Our first and most basic measure was whether the frog stays alive. We tracked the number of deaths over a fixed window of game decisions and the cause of each death (car collision, drowning, or timeout). An agent that scores quickly but dies often is worse for us than one that plays safely and consistently, because each death erases progress toward completing a level.

### 2. Goal Completion

We also tracked how many distinct lily pads the agent filled per level. Because Frogger requires hitting all five distinct win slots to advance, an agent that scores the same lily pad five times is failing. One of our major roadblocks was getting our agent to fill empty win slots, instead of repeatedly dying by trying to fill the same one over and over again. Because of the conditions of the game, we treated "Filled all 5 distinct slots" as the real success criterion for a level.

### 3. Decision Efficiency

Even when the agent doesn't die, it can be slow due to dawdling. We counted the number of game decisions between successive goal scores, and watched for dawdling behaviors like oscillating between actions and hesitating at the goal row. When we noticed the agent making 8-10 wasted decisions waiting for a log, we knew the heuristic was rewarding comfortable but unproductive states too much, and that caused us to implement specific improvements like the time-urgency penalty and the safe-lane penalty. 

In addition to these quantitative measures, we also relied on strenuous trace inspection. Whenever the agent made an obviously wrong choice, we would print the state, run MCTS once more from that state, and inspect the Q-values and visit counts for each action. This is how we caught several unapparent bugs like the mean Q-backup being poisoned by a single bad rollout, the potential function rewarding "near a goal slot" without distinguishing inside vs. outside the slot range, and the simulator's tick rate being out of sync with the real game.

Concretely, the final agent was measured against the following success criteria, all of which were met:

*Zero deaths* across six different trials in 120-decision games.

*All 5 distinct lily pads filled* per level, rather than the same slot scored repeatedly.

*No catastrophic failures* (walking blindly into water, getting permanently stuck, staying on a log long after it leaves the state space, etc)

All that being said, the biggest signal that the agent was actually working was watching it play multiple times and seeing the same behavior we wanted to see. Crossing the road decisively, riding a log and hopping to the next one, targeting a lily pad, and then reaching and repeating the process without dying. When the same approach reproduces success across different random conditions, for us that was the strongest evidence that both the search and heuristic are doing the right thing rather than getting lucky.




