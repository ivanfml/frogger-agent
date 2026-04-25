import copy
import random as Random 


#constants come from frogger.py

ACTIONS = ["up", "down", "left", "right", "stay"]

#lane y-vals for cars and logs (from frogger.py spawn positions)
CAR_LANES = [436, 397, 357, 318, 280]
LOG_LANES = [200, 161, 122, 83, 44]

#per-lane spawn configuration is (base_ticks, start_x, dir, factor)

CAR_CONFIGS = [
    (40, -55, "right", 1),
    (30, 506, "left", 2),
    (40, -80, "right", 2),
    (30,  506, "left",  1),
    (50, -56,  "right", 1),
]

#per-lane spawn configuration for logs (same format as above)
LOG_CONFIGS = [
    (30, -100, "right"),
    (30, 448, "left"),
    (40, -100, "right"),
    (40, 448, "left"),
    (20, -100, "right"),
]


#x-ranges for goal spots for the frog is (x_min, x_max, center_x)
GOAL_SLOTS = [
    (33, 53, 43),
    (115, 135, 125),
    (197, 217, 207),
    (279, 299, 289),
    (361, 381, 371),
]

FROG_INITIAL_POS = [207, 475]

#collision bounds
CAR_DESTROY_LEFT  = -80
CAR_DESTROY_RIGHT = 516
LOG_DESTROY_LEFT  = -100
LOG_DESTROY_RIGHT = 448

#zone thresholds
STREET_THRESHOLD = 240   
RIVER_LOW        = 40    
GOAL_THRESHOLD   = 40

#state data class, dict-of-dicts so its simple

def make_car(x, y, direction, factor):
    return {"x": x, "y": y, "direction": direction, "factor": factor}

def make_log(x, y, direction):
    return {"x": x, "y": y, "direction": direction}

def capture_state(frog, enemys, plataforms, chegaram, game, ticks_enemys,
                  ticks_plataforms, ticks_time):
    
    #dict shows full game state.
    #parameters that aren't obvious are as follows:
    #chegaram : list of arrived-frog objects (only count is needed)
    #ticks_enemys    : list[float] - spawn countdown timers for cars
    #ticks_plataforms: list[float] - spawn countdown timers for logs
    #ticks_time      : int - tick countdown within the current second

    return {
       "frog_x":               frog.position[0],
        "frog_y":               frog.position[1],
        "frog_lives":           frog.lives,
        "frog_animation_counter": frog.animation_counter,
        "frog_can_move":        frog.can_move,
        
        "cars": [
            make_car(e.position[0], e.position[1], e.way, e.factor)
            for e in enemys
        ],

        "logs": [
            make_log(p.position[0], p.position[1], p.way)
            for p in plataforms
        ],


        "goals_filled": len(chegaram),

        "speed":           game.speed,
        "level":           game.level,
        "time":            game.time,    
        "ticks_time":      ticks_time,

        "ticks_enemys":    list(ticks_enemys),
        "ticks_plataforms": list(ticks_plataforms),
    }

# SUCCESSOR STUFF

def _move_Frog(state,action):
    # Same as in moveFrog except they model frog animation as three sub-ticks whilst we just
    # care about one tick movement
    frog_x, frog_y = state["frog_x"], state["frog_y"]
 
    if action == "up":
        if frog_y > 39:
            frog_y -= 39          # 3 sub-ticks of 13px each
    elif action == "down":
        if frog_y < 473:
            frog_y += 39
    elif action == "left":
        if frog_x > 2:
            frog_x -= 41          # 2 sub-ticks of 14px + 1 of 13px = 41px
    elif action == "right":
        if frog_x < 401:
            frog_x += 41
 
    state["frog_x"] = frog_x
    state["frog_y"] = frog_y

# returns true if time is over (thus lost a life)
def _update_time(state):
    # 30 ticks = 1 sec = 1 "time"
    if state["ticks_time"] <= 0:
        state["ticks_time"] = 30
        state["time"] -= 1
    else:
        state["ticks_time"] -= 1
 
    if state["time"] <= 0:
        return True
    return False

def _frog_dead(state):
    state["frog_x"] = FROG_INITIAL_POS[0]
    state["frog_y"] = FROG_INITIAL_POS[1]
    state["frog_lives"] -= 1
    state["time"] = 30
    state["ticks_time"] = 30

# same purpose as createEnemys() + createPlataform()
def _spawn_obstacles(state):
    speed = state["speed"]
    level = state["level"]
 
    te = state["ticks_enemys"] # list of tick (int) where index is the car
    for i in range(len(te)):
        te[i] -= 1
        if te[i] <= 0:
            base, start_x, direction, factor = CAR_CONFIGS[i]
            te[i] = (base * speed) / level
            lane = CAR_LANES[i]
            state["cars"].append(make_car(start_x, lane, direction, factor))
 
    tp = state["ticks_plataforms"]
    for i in range(len(tp)):
        tp[i] -= 1
        if tp[i] <= 0:
            base, start_x, direction = LOG_CONFIGS[i]
            tp[i] = (base * speed) / level
            lane = LOG_LANES[i]
            state["logs"].append(make_log(start_x, lane, direction))

# same purpose as moveList() but both cars and logs in one
def _move_obstacles(state):
    speed = state["speed"]
 
    for car in state["cars"]:
        if car["direction"] == "right":
            car["x"] += speed * car["factor"]
        else:
            car["x"] -= speed * car["factor"]
 
    for log in state["logs"]:
        if log["direction"] == "right":
            log["x"] += speed
        else:
            log["x"] -= speed

# same purpose as carChangeRoad but better
def _car_Change_Road(state):
    car = Random.choice(state["cars"])

    if Random.randint(1, 2) == 2:
        shift = 39 
    else: 
        shift = -39

    new_y = car["y"] + shift

    if 280 <= new_y <= 436:
        car["y"] = new_y

# same purpose as frogOnTheStreet()
# Returns true on car collision
def _check_car_collision(state):
    frog_x = state["frog_x"]
    frog_y = state["frog_y"]
 
    frog_left   = frog_x
    frog_right  = frog_x + 30
    frog_top    = frog_y
    frog_bottom = frog_y + 30

    # widths from (sprite_car#.get_width())
    # lane 436 -> car1: 55px, lane 397 -> car2 58px, etc
    car_widths = {436: 55, 397: 58, 357: 80, 318: 68, 280: 56}
    for car in state["cars"]:
        if car["y"] in car_widths:
            car_width = car_widths[car["y"]]
        else:
            car_width = 58
            print("CAR Y NOT FOUND\n") # who knows
        car_left   = car["x"]
        car_right  = car["x"] + car_width
        car_top    = car["y"]
        car_bottom = car["y"] + 30
 
        if (frog_left < car_right and frog_right > car_left and
                frog_top < car_bottom and frog_bottom > car_top):
            return True
 
    return False

# same purpose as frogInTheLake()
# Returns true if frog is on a log
def _frog_on_log(state):
    frog_x = state["frog_x"]
    frog_y = state["frog_y"]
    speed  = state["speed"]
 
    # Frog is 30x30 (from frog.rect())
    frog_left   = frog_x
    frog_right  = frog_x + 30
    frog_top    = frog_y
    frog_bottom = frog_y + 30
 
    for log in state["logs"]:
        # Log sprite 99x30  (from sprite_plataform.get_width())
        log_left   = log["x"]
        log_right  = log["x"] + 99
        log_top    = log["y"]
        log_bottom = log["y"] + 30
 
        if (frog_left < log_right and frog_right > log_left and
                frog_top < log_bottom and frog_bottom > log_top):
            
            if log["direction"] == "right":
                state["frog_x"] += speed
            else:
                state["frog_x"] -= speed
            return True  
 
    return False

# same purpose as frogArrived()
def _check_goal(state):
    frog_x = state["frog_x"]
 
    for x_min, x_max, _ in GOAL_SLOTS:
        if x_min < frog_x < x_max:
            reward = 10 + state["time"]  # COULD MODIFY TO SEE WHICH WORKS BETTER
            state["goals_filled"] += 1
            state["frog_x"] = FROG_INITIAL_POS[0]
            state["frog_y"] = FROG_INITIAL_POS[1]
            state["time"]   = 30
            state["ticks_time"] = 30
 
            # Level done
            if state["goals_filled"] == 5:
                state["goals_filled"] = 0
                state["level"] += 1
                state["speed"] += 1
                return reward + 100  # COULD MODIFY TO SEE WHICH WORKS BETTER
 
            return reward
 
    # CHECK
    state["frog_y"] = 46
    return 0

# same purpose as destroyEnemys() + destroyPlataforms()
def _destroy_obstacles(state):
    state["cars"] = [
        car for car in state["cars"]
        if CAR_DESTROY_LEFT <= car["x"] <= CAR_DESTROY_RIGHT
    ]
    state["logs"] = [
        log for log in state["logs"]
        if LOG_DESTROY_LEFT <= log["x"] <= LOG_DESTROY_RIGHT
    ]


# stoc states whether or not the stochastic part (possible that car shifts lane) is active 
# stoc might be useful later idk. If not, then can delete it
# Returns:
# next_State: dict
# reward: float
# done: bool (true if the frog is out of lives)
# info: dict (cause: the reason for why the game is over) <- might be useful later idk
def generate_Successors(state, action, stoc=True):
    s = copy.deepcopy(state)
    reward = 0
    done   = False
    info   = {"cause": None}
    # move frog

    _move_Frog(s,action)

    # tick time
    time_over = _update_time(s)
    if time_over:
        _frog_dead(s)
        info["cause"] = "TIMEOUT"
        if s["frog_lives"] <= 0:
            done = True
        return s, reward, done, info
    
    # spawn obstacles
    _spawn_obstacles(s)

    # move obstacles
    _move_obstacles(s)

    # lane change
    # The successor might have a random car lane switch since the successors are not fully deterministic
    # (good for mcts)
    if stoc and s["cars"] and (Random.randint(0, 100) % 100 == 0):
        _car_Change_Road(s)

    # area check (collision, drown, goal)
    frog_y = s["frog_y"]
 
    if frog_y > STREET_THRESHOLD:
        # frog is in the road
        if _check_car_collision(s):
            _frog_dead(s)
            info["cause"] = "CAR COLLISION"
            if s["frog_lives"] <= 0:
                done = True
            return s, reward, done, info
 
    elif RIVER_LOW < frog_y < STREET_THRESHOLD:
        # frog is in the river
        safe = _frog_on_log(s)
        if not safe:
            _frog_dead(s)
            info["cause"] = "DROWNED"
            if s["frog_lives"] <= 0:
                done = True
            return s, reward, done, info
 
    elif frog_y < GOAL_THRESHOLD:
        # frog is in goal?
        reward = _check_goal(s)
        if reward > 0:
            info["cause"] = "GOAL"
    
    # clean up
    _destroy_obstacles(s)

    return s, reward, done, info