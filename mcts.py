import math
import random as Random
from state_space import generate_Successors, ACTIONS

#Could change the values of these to whatever you want
ITERATIONS = 300
MAX_DEPTH = 25
UCB_C = 1.41 # 1.41 = sqrt(2) which is supposed to be the norm
DISCOUNT = 0.95

# Change this if you want (was just testing things myself)
REWARD_GOAL =  100.0 # frog reaches a goal slot
REWARD_DEATH = -500.0 # frog loses a life
REWARD_STEP =    0.0 # neutral tick (no event)

# You can use these if you need them
FROG_START_Y = 475
GOAL_Y = 39
ROAD_TOP_Y = 240 # y >= this is road, y < this is river
LOG_ROW_Y = [200, 161, 122, 83, 44]  # river row y-values bottom to top
SAFE_LANES = [(460, 476), (241, 260)] # safe horizontal "lanes" (no cars, no water)
LOG_WIDTH = 99 
FROG_WIDTH = 30
FROG_HEIGHT = 30

W_PROGRESS = 4.0
W_CAR_DANGER = 25.0

_FROG_W = 30
_FROG_H = 30
_CAR_WIDTHS = {436: 55, 397: 58, 357: 80, 318: 68, 280: 56}
_START_Y = 475
_GOAL_Y_THRESHOLD = 40
_ROAD_TOP = 240

# Evaluate the state to return a reward
# Could also change the policy used in rollout for a better one (just random rn)

def _potential(state):
    if state["frog_lives"] <= 0:
        return 0.0
    
    frog_x = state["frog_x"]
    frog_y = state["frog_y"]
    phi = 0.0

    progress = (_START_Y - frog_y) / float(_START_Y - _GOAL_Y_THRESHOLD)
    phi += W_PROGRESS * 100.0 * progress

    if frog_y > _ROAD_TOP:
        phi -= W_CAR_DANGER * _car_threat(state, frog_x, frog_y, state["speed"])

    return phi

def _evaluate(state):
    if state["frog_lives"] <= 0:
        return REWARD_DEATH
    return _potential(state)

def _car_threat(state, frog_x, frog_y, speed):
    if not _CAR_WIDTHS:
        return 0.0
    lane = min(_CAR_WIDTHS.keys(), key=lambda L: abs(L - frog_y))
    if abs(lane - frog_y) > 20:
        return 0.0
    

    danger = 0.0
    frog_left, frog_right = frog_x, frog_x + _FROG_W
    for car in state["cars"]:
        if abs(car["y"] - lane) > 20:
            continue
        cw = _CAR_WIDTHS.get(car["y"], 60)
        car_left, car_right = car["x"], car["x"] + cw

        dx = speed * car.get("factor", 1)
        if car["direction"] == "right":
            future_left = car_left
            future_right = car_right + 2 * dx
        else:
            future_left = car_left - 2 * dx
            future_right = car_right

        if future_left < frog_right and future_right > frog_left:
            gap = min(abs(car_left - frog_right), abs(car_right - frog_left))
            danger += max(0.2, 1.0 - gap / 150.0)
    return danger

# Just testing (doesnt really work at all)
def _reward_from_info(info):
    if info["cause"] == "GOAL":
        return REWARD_GOAL
    elif info["cause"] in ("CAR COLLISION", "DROWNED", "TIMEOUT"):
        return REWARD_DEATH
    return REWARD_STEP

def _rollout(state, node, depth):
    if depth == 0:
        return 0.0

    if state["frog_lives"] <= 0:
        return REWARD_DEATH

    action = Random.choice(ACTIONS)   # pi_0: uniform random

    next_state, _, done, info = generate_Successors(state, action, stoc=True)
    # r = _reward_from_info(info)
    r = _evaluate(next_state)

    if done:
        return r

    if action not in node.children:
        node.children[action] = MCTSNode(next_state, parent=node, action_taken=action)

    return r + DISCOUNT * _simulate(next_state, node.children[action], depth - 1, node.n_self)


def _simulate(state, node, depth, parent_n):
    if depth == 0:
        return 0.0

    if state["frog_lives"] <= 0:
        return REWARD_DEATH

    if node.n_self == 0:
        return _rollout(state, node, depth)
    
    log_parent = math.log(parent_n) if parent_n > 0 else 0.0

    def ucb(a):
        if node.n_sa[a] == 0:
            return float("inf")
        return node.q_sa[a] + UCB_C * math.sqrt(log_parent / node.n_sa[a])
    
    # a <- argmax UCB
    action = max(ACTIONS, key=ucb)

    next_state, _, done, info = generate_Successors(state, action, stoc=True)
    # r = _reward_from_info(info)
    r = _evaluate(next_state)

    if action not in node.children:
        node.children[action] = MCTSNode(next_state, parent=node, action_taken=action)

    child = node.children[action]

    if done:
        q = r
    else:
        q = r + DISCOUNT * _simulate(next_state, child, depth - 1, node.n_self)

 
    node.n_sa[action] += 1
    node.q_sa[action] += (q - node.q_sa[action]) / node.n_sa[action]
    node.n_self += 1

    return q

class MCTSNode:
    def __init__(self, state, parent=None, action_taken=None):
        self.state = state
        self.parent = parent
        self.action_taken = action_taken
        self.children = {}                     
        self.n_self = 0  # N(s) this node's own visit count (used by children as parent_n) (so sum of all N(s,a))
        self.n_sa = {a: 0   for a in ACTIONS}  # N(s,a) how many times each action was selected from here
        self.q_sa = {a: 0.0 for a in ACTIONS}  # Q(s,a) action value utility for each action

 
def mcts_decision(state, iterations=ITERATIONS):
    root = MCTSNode(state)

    for _ in range(iterations):
        _simulate(state, root, MAX_DEPTH, root.n_self)

    # argmax_a Q(s,a)
    return max(ACTIONS, key=lambda a: root.q_sa[a])