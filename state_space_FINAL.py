#state_spaceFINAL.py

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