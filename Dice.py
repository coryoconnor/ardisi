
import random

class d: BLACK = 'black'; BLUE = 'blue'; RED = 'red';
class df: MISS = 'miss'; HIT = 'hit'; ACC = 'accuracy'; CRIT = 'crit'; HITHIT = 'hithit'; CRITHIT = 'crithit';
class distance: SHORT = 'short'; MEDIUM = 'medium'; LONG = 'long';
class dtoken: BRACE = 'brace'; CONTAIN = 'contain'; EVADE = 'evade'; REDIRECT = 'redirect'; SCATTER = 'scatter';
class etype: CANCEL = 'cancel'; REROLL = 'reroll'
class player: ATTACKER = 'Attacker'; DEFENDER = 'Defender'

valid_distance_colors = { distance.SHORT:[d.RED, d.BLACK, d.BLUE], distance.MEDIUM:[d.RED, d.BLUE], distance.LONG:[d.RED] }
sides_dict = {d.RED:(df.HIT, df.HIT, df.HITHIT, df.CRIT, df.CRIT, df.ACC, df.MISS, df.MISS),
              d.BLUE: (df.HIT, df.HIT, df.HIT, df.HIT, df.CRIT, df.CRIT, df.ACC, df.ACC),
              d.BLACK: (df.HIT, df.HIT, df.HIT, df.HIT, df.CRITHIT, df.CRITHIT, df.MISS, df.MISS)}

expected_hits_cache = { }

def expected_hits(color, critsmatter):
    if expected_hits_cache.has_key((color, critsmatter)):
        return expected_hits_cache[(color, critsmatter)]
    else:
        hits = 0
        for side in sides_dict[color]:
            if side == df.HIT: hits += 1
            elif side == df.HITHIT: hits += 2
            elif side == df.CRIT:
                if critsmatter: 
                    hits += 1
            elif side == df.CRITHIT: 
                hits += 1
                if critsmatter:
                    hits += 1
    expected_hits_cache[(color, critsmatter)] = float(hits)/len(sides_dict[color])
    return expected_hits_cache[(color, critsmatter)]

def initial_roll(combat_spec):
    result = {}
    for color in combat_spec.attack_dice.keys():
        numdice = combat_spec.attack_dice[color]
        if numdice == 0:
            continue
        if color not in valid_distance_colors[combat_spec.attack_distance]:
            combat_spec.add_event(str(numdice) + ' dice of color ' + color + ' cannot shoot at ' + combat_spec.attack_distance + ' range. Removing these dice.')
            continue
        if color not in sides_dict.keys():
            raise Exception('ERROR: Attempting to roll color ' + color + ' dice.')
        if numdice < 0 or numdice > 10:
            raise Exception('ERROR: Attempting to roll ' + numdice + ' dice.')
        rolls = []
        for _ in xrange(numdice):
            rolls.append(rollsingle(color))
        if len(rolls) > 0:
            result[color] = sorted(rolls)
    combat_spec.add_event('Initial roll result was: ' + str(result) + ' ==> ' + summarize_die(result, True, True))
    return result

def rollsingle(color):
    return random.choice(sides_dict[color])

def count_accuracies(roll_dict):
    accuracies = 0
    for _, rolls in roll_dict.items():
        for roll in rolls:
            if roll == df.ACC:
                accuracies += 1
    return accuracies

### OFFENSIVE STUFF

def find_item_in_strategy(combat_spec, strategy):
    for color, dice in strategy:
        if color in combat_spec.current_roll.keys():
            if dice in combat_spec.current_roll[color]:
                return (color, dice)
    return None

pure_dmg_reroll_strat = [(d.BLACK, df.MISS), (d.RED, df.MISS), (d.RED, df.ACC), (d.BLUE, df.ACC), (d.BLACK, df.HIT)]
dmg_hold_acc_reroll_strat = [(d.BLACK, df.MISS), (d.RED, df.MISS), (d.BLACK, df.HIT)]
blue_acc_reroll_strat = [(d.BLUE, df.HIT), (d.BLUE, df.CRIT), (d.RED, df.MISS), (d.BLACK, df.MISS), (d.BLACK, df.HIT)]
force_accuracy_reroll_strat = [(d.BLUE, df.HIT), (d.BLUE, df.CRIT), (d.RED, df.MISS), (d.RED, df.HIT), (d.RED, df.CRIT), (d.RED, df.HITHIT)]

def reroll(combat_spec, reroll_pair, player, ability):
    color, dice = reroll_pair
    new_dice = rollsingle(color)
    combat_spec.current_roll[color].remove(dice)
    combat_spec.current_roll[color].append(new_dice)
    combat_spec.add_event(player + ' used [' + ability + '] to reroll a [' + color + '] [' + dice + '] to a [' + new_dice + '], result became: ' + 
                          str(combat_spec.current_roll) + ' ==> ' + summarize_die(combat_spec.current_roll, True, True))

def concentrate_fire_dial_roll(combat_spec, color):
    new_roll = rollsingle(color)
    combat_spec.current_roll[color].append(new_roll)
    combat_spec.add_event('Attacker used [CONCENTRATE_FIRE_DIAL] to roll a [' + color + '] [' + new_roll + ']. Result became: ' + 
                          str(combat_spec.current_roll) + ' ==> ' + summarize_die(combat_spec.current_roll, True, True))
    combat_spec.oabilities_used.append('CONCENTRATE_FIRE_DIAL')
    combat_spec.conc_fire_dial = False

evade_color_preference = [d.BLUE, d.RED, d.BLACK]
damage_color_preference = [d.BLACK, d.RED, d.BLUE]

def mitigate_scatter(combat_spec):
    color = None
    accuracy_count = count_accuracies(combat_spec.current_roll)
    stok = combat_spec.defense_tokens[dtoken.SCATTER]
    if stok > accuracy_count:
        for pot_color in evade_color_preference:
            if pot_color in combat_spec.current_roll.keys(): 
                color = pot_color
                if pot_color is not d.BLACK:
                    combat_spec.add_event('Defender has scatter token - attacker adding [' + color + '] die to get an accuracy.')
                else:
                    combat_spec.add_event('Defender has scatter token - No dice available to add to accuracy, using black die instead.')
                concentrate_fire_dial_roll(combat_spec, color)
                return True
    return False

def mitigate_evade(combat_spec):
    accuracy_count = count_accuracies(combat_spec.current_roll) - combat_spec.defense_tokens[dtoken.SCATTER]
    etok = combat_spec.defense_tokens[dtoken.EVADE]
    if etok - accuracy_count == 1 and combat_spec.current_roll.has_key(d.BLUE):
        color = d.BLUE
        combat_spec.add_event('Attacker adding [blue] die to get an accuracy to nullify evade.')
    else:
        for pot_color in damage_color_preference:
            if pot_color in combat_spec.current_roll.keys():
                color = pot_color
                break
        combat_spec.add_event('Attacker adding any die to maximize damage.')
    concentrate_fire_dial_roll(combat_spec, color)
    return True

def add_offensive_die(combat_spec):
    if mitigate_scatter(combat_spec): return
    if mitigate_evade(combat_spec): return

def offensive_reroll(combat_spec):
    strat = None
    accuracy_count = count_accuracies(combat_spec.current_roll)
    stok = combat_spec.defense_tokens[dtoken.SCATTER]
    etok = combat_spec.defense_tokens[dtoken.EVADE]
    if stok > accuracy_count:
        strat = force_accuracy_reroll_strat
        combat_spec.add_event('Attacker rerolling to try and cancel defensive scatter token(s).'.format(accuracy_count, etok))
    elif combat_spec.attack_distance == distance.SHORT:
        strat = pure_dmg_reroll_strat
        combat_spec.add_event('At short range defender is not able to evade, attacker rerolling any dice to maximize damage.'.format(accuracy_count, etok))
    elif accuracy_count > etok + stok:
        strat = pure_dmg_reroll_strat
        combat_spec.add_event('{0} accuracies ({1} needed), attacker rerolling any dice to maximize damage.'.format(accuracy_count, etok + stok))
    elif accuracy_count == etok + stok:
        strat = dmg_hold_acc_reroll_strat
        combat_spec.add_event('{0} accuracies ({1} needed), attacker rerolling non-accuracies to maximize damage.'.format(accuracy_count, etok + stok))
    elif (etok + stok) - accuracy_count == 1:
        strat = blue_acc_reroll_strat 
        combat_spec.add_event('{0} accuracies ({1} needed), attacker rerolling to get an accuracy first or maximize damage if impossible.'.format(accuracy_count, etok + stok))
    elif (etok + stok) - accuracy_count > 1:
        strat = pure_dmg_reroll_strat 
        combat_spec.add_event('{0} accuracies ({1} needed), attacker rerolling any dice to maximize damage.'.format(accuracy_count, etok + stok))
    reroll_pair = find_item_in_strategy(combat_spec, strat)
    if reroll_pair is not None:
        reroll(combat_spec, reroll_pair, player.ATTACKER, 'CONCENTRATE_FIRE_TOKEN')
        combat_spec.oabilities_used.append('CONCENTRATE_FIRE_TOKEN')
        combat_spec.conc_fire_token = False
    else:    
        combat_spec.add_event('There is no reliable strategy to improve the current roll by using a [CONCENTRATE_FIRE_TOKEN].')

def find_accuracy(combat_spec):
    for color, die_list in combat_spec.current_roll.items():
        for die in die_list:
            if die is df.ACC:
                return color
    return None

def accuracies_allocated(combat_spec, dtoken_type):
    if combat_spec.allocated_accuracies.has_key(dtoken_type):
        return len(combat_spec.allocated_accuracies[dtoken_type])
    else:
        return 0
    
def allocate_accuracy(combat_spec, color, dtoken_type):
    combat_spec.current_roll[color].remove(df.ACC)
    if not combat_spec.allocated_accuracies.has_key(dtoken_type):
        combat_spec.allocated_accuracies[dtoken_type] = []
    combat_spec.allocated_accuracies[dtoken_type].append((color, df.ACC))
    combat_spec.add_event('Attacker allocated [{0}] [accuracy] to [{1}] defense token.'.format(color, dtoken_type))

def allocate_accuracies(combat_spec):
    accuracy_count = count_accuracies(combat_spec.current_roll)
    while accuracy_count > 0:
        stok_remain = combat_spec.defense_tokens[dtoken.SCATTER] - accuracies_allocated(combat_spec, dtoken.SCATTER)
        etok_remain = combat_spec.defense_tokens[dtoken.EVADE] - accuracies_allocated(combat_spec, dtoken.EVADE)
        if stok_remain > 0:
            color = find_accuracy(combat_spec)
            allocate_accuracy(combat_spec, color, dtoken.SCATTER)
            accuracy_count -= 1
        elif etok_remain > 0:
            color = find_accuracy(combat_spec)
            allocate_accuracy(combat_spec, color, dtoken.EVADE)
            accuracy_count -= 1
        else:
            break
            
### DEFENSIVE STUFF

def can_evade(combat_spec):
    evade_type = None
    if combat_spec.attack_distance == distance.SHORT:
        combat_spec.add_event('Defender cannot use evade tokens at short range.')
        return False, evade_type
    num_evades = combat_spec.defense_tokens[dtoken.EVADE]
    if num_evades < 1:
        raise Exception('ERROR: Evades is set to: ' + str(combat_spec.defense_tokens[dtoken.EVADE]) + ', please enter a positive integer for the number of evades')
    if combat_spec.attack_distance == distance.MEDIUM:
        evade_type = etype.REROLL
    if combat_spec.attack_distance == distance.LONG:
        evade_type = etype.CANCEL
    accuracies = count_accuracies(combat_spec.current_roll)
    evadable = num_evades > accuracies
    return evadable, evade_type

cancel_roll_order = [df.CRITHIT, df.HITHIT, df.CRIT, df.CRIT]
def evade_cancel(combat_spec):
    for roll in cancel_roll_order:
            for color, rolls in combat_spec.current_roll.items():
                if roll in rolls:
                    rolls.remove(roll)
                    combat_spec.add_event('Defender used [EVADE_DEFENSE_TOKEN] to cancel a [' + color + '] [' + roll + ']')
                    return True
    return False

evade_reroll_strategy = [(d.RED, df.HITHIT), (d.BLACK, df.CRITHIT), (d.BLUE, df.CRIT), (d.RED, df.CRIT), (d.BLUE, df.HIT), (d.RED, df.HIT)]
def perform_evade(combat_spec, evade_type):
    evaded = False
    if evade_type == etype.CANCEL:
        evaded = evade_cancel(combat_spec)
    if evade_type == etype.REROLL:
        reroll_pair = find_item_in_strategy(combat_spec, evade_reroll_strategy)
        if reroll_pair != None:
            reroll(combat_spec, reroll_pair, player.DEFENDER, 'EVADE_DEFENSE_TOKEN')
            evaded = True
    if evaded:
        combat_spec.dabilities_used.append('EVADE_DEFENSE_TOKEN')
                        
def summarize_die(result, crits_are_hits=True, crits_matter=True):
    hits = 0
    accuracies = 0
    critical = False
    for _, rolls in result.items():
        for roll in rolls:
            if roll == df.MISS:
                continue
            if roll == df.HIT:
                hits += 1
                continue
            if roll == df.ACC:
                accuracies += 1
                continue
            if roll == df.CRIT:
                if crits_are_hits:
                    hits += 1
                if crits_matter:
                    critical = True
                continue
            if roll == df.HITHIT:
                hits += 2
                continue
            if roll == df.CRITHIT:
                hits += 1
                if crits_are_hits:
                    hits += 1
                if crits_matter:
                    critical = True
                continue
            raise Exception('ERROR: strange dice face: ' + roll)     
    txtresult = ''
    if hits > 0:
        txtresult += str(hits)
    else:
        return '0'
    if critical:
        txtresult += 'C'
    if accuracies > 0:
        txtresult += accuracies * 'A'
    return txtresult
