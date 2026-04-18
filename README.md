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
Run `python frogger.py`

## State Space Specification

### Mathematical description of States, Transitions, Actions and Rewards
 
A **state** $s \in S$ is a tuple:
 
$$s = (p,\ C,\ L,\ g,\ t,\ v)$$

where: 
- $p = (x_f, y_f) \in \mathbb{Z}^2$ — frog pixel position, with $x_f \in [2, 401]$ and $y_f \in [39, 475]$
- $C = \\{(x_i^c,\ y_i^c,\ d_i^c,\ k_i)\\}$ — for $i=1, 2, \cdots, n_c$ active cars, where $x_i^c$ is x position, $y_i^c \in \\{280, 318, 357, 397, 436\\}$ is for y position, $d_i^c \in \\{\text{left}, \text{right}\\}$ is for direction, and $k_i \in \\{1, 2\\}$ is the speed factor
- $L = \\{(x_j^l,\ y_j^l,\ d_j^l)\\}$ — active logs, where $y_j^l \in \\{44, 83, 122, 161, 200\\}$
- $g \in \\{0,1\\}^5$ — which goal slots are filled
- $t \in \\{0, \ldots, 30\\}$ — remaining time steps
- $v \in \mathbb{Z}^+$ — current game speed (starts at 3, goes up each level)
 
**Actions:** At each tick the agent picks one of:
 
$$A = \\{\text{up},\ \text{down},\ \text{left},\ \text{right},\ \text{stay}\\}$$
 
Up/down actions move $y_f$ by ±13px per animation step. Left/right actions move $x_f$ by ±13 or ±14px. The stay action does not change frog position. Movement is blocked at the screen bounds ($x_f \in [2, 401]$ and $y_f \in [39, 475]$).
 
**Transitions:** $T(s, a) \to s'$:
 
Deterministic part (every tick):
- Each car moves: $x_i^c += v \cdot k_i$ if going right or $x_i^c\ -= v \cdot k_i$ if going left. Cars outside bounds are removed.
- Each log moves: $x_j^l += v$ if going right or $x_j^l-= v$ if going left. Logs outside bounds are removed.
- New cars/logs spawn when their countdown timers hit 0.
- If the frog is in the river zone and on a log, $x_f$ moves by $\pm v$ each tick even without agent action.
- The frog's position updates according to $a$.
- $t' = t - 1$, if $t' = 0$ the frog loses a life and resets.
 
Stochastic part (1% chance per tick):
- One car is chosen at random and it moves to a different lane by ±39px in y, bounded to $y \in [280, 436]$. So, 

So, the state that the agent transition to depends on whether or not 1% chance hit or not.
 
**Rewards:**
- $R = 0$ each tick
- $R = 10 + t$ when the frog reaches a goal slot (give a bonus if the frog gets to the goal quicker)
- $R = 100$ when all 5 goals are filled (level complete)
- $R = - \infty$ or $-100$ on car collision, drowning, or timeout