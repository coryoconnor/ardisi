
import string
import math
import random
from copy import deepcopy

from Dice import summarize_die, initial_roll, offensive_reroll, add_offensive_die, allocate_accuracies, accuracies_allocated
from Dice import perform_evade, can_evade, dtoken

class hull: DEFENDING = 'defending'; ADJACENT = 'adjacent'; OPPOSITE = 'opposite'

def init(initial_combat_spec):
    combat_spec = deepcopy(initial_combat_spec)
    if combat_spec.seed == None:
        combat_spec.seed = random.randint(1, 10000000)
    random.seed(combat_spec.seed)
    return combat_spec

def defensive_evade(combat_spec):
    etok_remain = combat_spec.defense_tokens[dtoken.EVADE] - accuracies_allocated(combat_spec, dtoken.EVADE)
    if etok_remain > 0:
        evadable, evade_type = can_evade(combat_spec)
        if evadable:
            perform_evade(combat_spec, evade_type)
            combat_spec.add_event('After defensive evade, result became: ' + str(combat_spec.current_roll) + ' ==> ' + summarize_die(combat_spec.current_roll, True, True))
            return True
    return False

def defensive_scatter(combat_spec):
    stok_remain = combat_spec.defense_tokens[dtoken.SCATTER] - accuracies_allocated(combat_spec, dtoken.SCATTER)
    if stok_remain > 0:
        combat_spec.add_event('Defender used [SCATTER_DEFENSE_TOKEN] to nullify attack.')
        combat_spec.dabilities_used.append('SCATTER_DEFENSE_TOKEN')
        combat_spec.current_roll = { }
        return True
    return False

def spend_defensive_tokens(combat_spec):
    tokens = []
    for token_type in [dtoken.BRACE, dtoken.CONTAIN, dtoken.EVADE, dtoken.REDIRECT, dtoken.SCATTER]:
        if combat_spec.defense_tokens[token_type] - accuracies_allocated(combat_spec, token_type) > 0:
            tokens.append(token_type)
    if len(tokens) > 0:
        combat_spec.add_event('The defender has the following defense tokens available to spend: ' + str(tokens))
    else:
        combat_spec.add_event('All defensive tokens have been nullified by accuracy dice.')
    scattered = defensive_scatter(combat_spec)
    if scattered: return
    evaded = defensive_evade(combat_spec)
    if evaded: return

def combat(initial_combat_spec):
    # HOUSEKEEPING
    combat_spec = init(initial_combat_spec)
    
    # INITIAL ATTACK ROLL
    combat_spec.current_roll = initial_roll(combat_spec)
    
    # CONCENTRATE FIRE TOKEN
    if combat_spec.conc_fire_token: offensive_reroll(combat_spec)
    # CONCENTRATE FIRE DIAL
    if combat_spec.conc_fire_dial: add_offensive_die(combat_spec)
    # RETRY TOKEN IN CASE IT WASN'T USED BUT NOW SHOULD BE TO REROLL DIAL DIE
    if combat_spec.conc_fire_token: offensive_reroll(combat_spec)
    
    # ALLOCATE ACCURACIES
    allocate_accuracies(combat_spec)
    
    # EVADE DEFENSE TOKEN
    spend_defensive_tokens(combat_spec)
    
    # RESULTS
    combat_spec.add_event('Final combat result ==> ' + summarize_die(combat_spec.current_roll, True, True))
    combat_spec.add_event('Offensive powers used: ' + str(combat_spec.oabilities_used))
    combat_spec.add_event('Defensive powers used: ' + str(combat_spec.dabilities_used))
    
    return combat_spec

def multi_combat_summary(results):
    num_results = len(results)
    damage_map = {}
    crit_map = {}
    total_damage = 0
    t1 = string.maketrans('','')
    nodigs = t1.translate(t1, string.digits)
    for combat_result in results:
        result = summarize_die(combat_result.current_roll, True, True)
        damage = int(result.translate(t1, nodigs))
        total_damage += damage
        if damage not in damage_map.keys():
            damage_map[damage] = 0
            crit_map[damage] = 0
        damage_map[damage] += 1
        if 'C' in result:
            crit_map[damage] += 1
    avg_dmg = float(total_damage) / num_results
    crit_likely = float(sum(crit_map.values())) / num_results
    print 'Average damage was: {0:.2} with an overall critical likelihood of {1:.1%}'.format(avg_dmg, crit_likely)
    for damage in sorted(damage_map.keys()):
        percent_occurence = float(damage_map[damage]) / num_results
        odds = int(math.floor(1/percent_occurence))
        percent_crit = float(crit_map[damage]) / damage_map[damage]
        print str(damage) + " damage is {:.3%} likely (1/{:}) with a critical effect {:.1%} of the time.".format(percent_occurence, odds, percent_crit)
    