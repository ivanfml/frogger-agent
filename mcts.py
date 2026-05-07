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
W_RIVER_SAFETY = 80.0
W_LOG_EDGE = 4.0
W_GOAL_LANE = 8.0
W_TIME_URGENCY = 8.0

_FROG_W = 30
_FROG_H = 30
_CAR_WIDTHS = {436: 55, 397: 58, 357: 80, 318: 68, 280: 56}
_GOAL_CENTERS = [43, 125, 207, 289, 371]
_GOAL_RANGES = [(33, 53), (115, 135), (197, 217), (279, 299), (361, 381)]
_LOG_W = 99
_START_Y = 475
_GOAL_Y_THRESHOLD = 40
_ROAD_TOP = 240
_RIVER_TOP = 40

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

    time_remaining = state.get("time", 30)
    phi -= W_TIME_URGENCY * (30 - time_remaining)

    if 241 <= frog_y <= 260:
        phi -= 50.0
    if 460 <= frog_y <= 476:
        phi -= 30.0

    if frog_y > _ROAD_TOP:
        phi -= W_CAR_DANGER * _car_threat(state, frog_x, frog_y, state["speed"])

    elif _RIVER_TOP < frog_y < _ROAD_TOP:
        log = _log_under_frog(state, frog_x, frog_y)
        if log is None:
            phi -= W_RIVER_SAFETY
        else:
            edge_dist = _log_edge_distance(log, frog_x)
            phi -= W_LOG_EDGE * max(0.0, (40.0 - edge_dist)) / 40.0
    
    if frog_y < _RIVER_TOP + 25:
        filled = state.get("filled_slots", set())
        open_centers = [cx for i, cx in enumerate(_GOAL_CENTERS) if i not in filled]
        open_ranges = [_GOAL_RANGES[i] for i in range(5) if i not in filled]
        filled_ranges = [_GOAL_RANGES[i] for i in range(5) if i in filled]
        if open_centers:
            frog_center_x = frog_x + _FROG_W // 2
            in_open_slot = any(lo < frog_x < hi for (lo, hi) in open_ranges)
            in_filled_slot = any(lo < frog_x < hi for (lo, hi) in filled_ranges)
            nearest = min(abs(frog_center_x - cx) for cx in open_centers)
            if in_open_slot:
                phi += 400.0
            elif in_filled_slot:
                phi -= 200.0
            phi -= 1.5 * nearest
    
    else:
        filled = state.get("filled_slots", set())
        open_centers = [cx for i, cx in enumerate(_GOAL_CENTERS) if i not in filled]
        if open_centers:
            climb_frac = max(0.0, (_START_Y - frog_y) / float(_START_Y - _GOAL_Y_THRESHOLD))
            nearest = min(abs(frog_x + _FROG_W // 2 - cx) for cx in open_centers)
            phi -= climb_frac * 0.3 * nearest

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

def _log_under_frog(state, frog_x, frog_y):
    fl, fr = frog_x, frog_x + _FROG_W
    ft, fb = frog_y, frog_y + _FROG_H
    for log in state["logs"]:
        ll, lr = log["x"], log["x"] + _LOG_W
        lt, lb = log["y"], log["y"] + _FROG_H
        if fl < lr and fr > ll and ft < lb and fb > lt:
            return log
    return None

def _log_under_frog_lookahead(state, frog_x, frog_y, speed):
    fl, fr = frog_x, frog_x + _FROG_W
    ft, fb = frog_y, frog_y + _FROG_H
    best = None
    best_overlap = 0
    for log in state["logs"]:
        if log["direction"] == "right":
            lx = log["x"] + 3 * speed
        else:
            lx = log["x"] - 3 * speed
        ll, lr_ = lx, lx + _LOG_W
        lt, lb = log["y"], log["y"] + _FROG_H
        if fl < lr_ and fr > ll and ft < lb and fb > lt:
            overlap = min(fr, lr_) - max(fl, ll)
            if overlap > best_overlap:
                best_overlap = overlap
                best = dict(log)
                best["x"] = lx
    return best

def _log_edge_distance_lookahead(log, frog_x, speed):
    log_left = log["x"]
    log_right = log["x"] + _LOG_W
    frog_left = frog_x
    frog_right = frog_x + _FROG_W

    left_gap = frog_left - log_left
    right_gap = log_right - frog_right

    if log["direction"] == "right":
        return max(0, left_gap)
    else:
        return max(0, right_gap)


def _log_edge_distance(log, frog_x):
    log_left = log["x"]
    log_right = log["x"] + _LOG_W
    frog_left = frog_x
    frog_right = frog_x + _FROG_W

    left_gap = frog_left - log_left
    right_gap = log_right - frog_right

    if log["direction"] == "right":
        return max(0, left_gap)
    else:
        return max(0, right_gap)

# Just testing (doesnt really work at all)
def _reward_from_info(info, prev_lives, new_lives):
    if new_lives < prev_lives:
        return REWARD_DEATH
    if info["cause"] == "GOAL":
        return REWARD_GOAL
    return REWARD_STEP

def _step_reward(prev_state, next_state, info):
    r = _reward_from_info(info, prev_state["frog_lives"], next_state["frog_lives"])
    shaping = _potential(next_state) - _potential(prev_state)
    return r + shaping

def _is_terminal(state, info):
    if state["frog_lives"] <= 0:
        return True
    if info.get("cause") in ("CAR COLLISION", "DROWNED", "TIMEOUT"):
        return True
    return False

def _rollout_action(state):
    best_a = None
    best_val = -float("inf")
    for a in ACTIONS:
        ns, _r, _d, info = generate_Successors(state, a, stoc=False)
        val = _potential(ns)
        if ns["frog_lives"] < state["frog_lives"]:
            val -= 2000.0
        if info.get("cause") == "GOAL":
            val += REWARD_GOAL
        if val > best_val:
            best_val = val
            best_a = a
    return best_a

def _rollout(state, depth):
    total = 0.0
    discount = 1.0
    cur = state
    rollout_depth = min(depth, 8)
    for _ in range(rollout_depth):
        action = _rollout_action(cur)
        next_state, _env_r, done, info = generate_Successors(cur, action, stoc=True)
        r = _step_reward(cur, next_state, info)
        total += discount * r
        discount *= DISCOUNT
        if done or _is_terminal(next_state, info):
            return total
        cur = next_state
    total += discount * _potential(cur)
    return total


def _simulate(state, node, depth, parent_n):
    if depth == 0:
        return 0.0

    if state["frog_lives"] <= 0:
        return REWARD_DEATH

    if node.n_self == 0:
        v = _rollout(state, depth)
        node.n_self += 1
        return v
    
    log_parent = math.log(parent_n) if parent_n > 0 else 0.0

    def ucb(a):
        if node.n_sa[a] == 0:
            return float("inf")
        return node.q_sa[a] + UCB_C * math.sqrt(log_parent / node.n_sa[a])
    
    # a <- argmax UCB
    action = max(ACTIONS, key=ucb)

    next_state, _env_r, done, info = generate_Successors(state, action, stoc=True)
   
    r = _step_reward(state, next_state, info)

    if action not in node.children:
        node.children[action] = MCTSNode(next_state, parent=node, action_taken=action)

    child = node.children[action]

    if done or _is_terminal(next_state, info):
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