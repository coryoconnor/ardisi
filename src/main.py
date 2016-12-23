
import multiprocessing 
import itertools

from Combat import combat, multi_combat_summary, hull
from Dice import d, distance, dtoken

###=========== EDIT THIS SECTION ================
class CombatSpec:
    def __init__(self, explain, seed=None):
        self.attack_dice = {d.RED: 0, d.BLACK: 5, d.BLUE: 2}
        self.current_roll = { }
        self.attack_distance = distance.SHORT
        self.defense_tokens = {dtoken.BRACE: 0, # DOESNT WORK
                               dtoken.CONTAIN: 0,  # DOESNT WORK
                               dtoken.EVADE: 1,
                               dtoken.REDIRECT: 0,  # DOESNT WORK
                               dtoken.SCATTER: 0}
        self.allocated_accuracies = { }
#         self.defender_shields = {hull.DEFENDING: 3, # DOESNT WORK
#                                  hull.ADJACENT: [2, 2], # DOESNT WORK
#                                  hull.OPPOSITE: 1} # DOESNT WORK
#         self.defender_hull = 4 # DOESNT WORK
        self.conc_fire_token = True
        self.conc_fire_dial = True
        self.oabilities = [] # DOESNT WORK ("DODONNA'S PRIDE", "DARTH VADER", "ADMIRAL SCREED", "ORDINANCE EXPERTS")
        self.oabilities_used = []
        self.dabilities = [] # DOESNT WORK ("MON MOTHMA", "FORESIGHT", "ADVANCED PROJECTORS")
        self.dabilities_used = []
        self.seed = seed
        self.event_log = []
        self.explain = explain
    
    def add_event(self, estr):
        if self.explain: print estr
        self.event_log.append(estr)

sim_mode = 'batch' # either batch or single - single explains everything during a single sim, batch runs a monte carlo
num_tests = 100000
###==============================================

if __name__ == '__main__':
    if sim_mode == 'single':
        spec = CombatSpec(explain=True)
        combat_result = combat(spec)
        print 'Random seed used: ' + str(combat_result.seed)
    elif sim_mode == 'batch':
        spec = CombatSpec(explain=False)
        combat_results = multiprocessing.Pool(16).map(combat, itertools.repeat(spec, num_tests))
        multi_combat_summary(combat_results)
    