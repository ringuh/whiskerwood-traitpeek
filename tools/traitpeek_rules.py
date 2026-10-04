"""TraitPeek base rules, INI style. Built into WBP_TraitPeek as one string (lines joined with '|').
The user's %localappdata%\\Whiskerwood\\Saved\\mods\\TraitPeekConfig\\TraitPeek.txt is read after
these and only adds to / changes them: rules apply top to bottom, a later line wins for a trait.
Sections: [groups] (name = building ids; a repeated name adds members) or a target
(all, fuel, nofuel, a group name, a building id) with keys green / yellow / red / neutral."""
GROUPS = [
    ('factory', 'Apothecary, Bakery, Blacksmith, BlastFurnace, Brickmaker, Cannery, CannonFoundry, carpenter, '
                'CoalSifter, CottonGin, fineKitchen, fishery, FlaxSpinner, lumbermill, Machinist, mill, netter, '
                'OilPress, OreSmelter, SailManufactory, SmallFurnace, SpiceGrinder, stewery, Tailor, Teaprocessor, '
                'Toolmaker, Weaver, SmallShipyard, Shipyard, GiantShipyard'),
    ('fuel', 'CoalSifter'),
    ('extraction', 'MiningCamp, WoodcuttersCamp, farm, Earthworks, Gatherer, ConstructionYard, LogisticsHub, FireTender'),
    ('service', 'FoodVending, fancyVending, Supplier'),
    ('office', 'CoordinationOffice, TriageBeds'),
    ('school', 'School'),
    ('research', 'researchBuilding, Laboratory'),
    ('fishing', 'fishing_dock'),
    ('docks', 'navaldock_scout, navaldock_fishing, navaldock_guano, navaldock_trade, navaldock_war, navaldock_hunting'),
]
TARGETS = [
    ('all', [('red', 'rude, nosey, greedy, heavyEater'), ('yellow', 'pessimist, slow')]),
    ('nofuel', [('red', 'sickly')]),
    ('fuel', [('green', 'nosmell')]),
    ('factory', [('green', 'rebellious, diligent'), ('red', 'monarchist, unsafeworker, mypace'), ('yellow', 'slow, weak, weakknees')]),
    ('extraction', [('green', 'warmCore, strongShoulders, swift, healthy'), ('red', 'weak, weakknees, rebellious, sickly, slow')]),
    ('service', [('green', 'swift, strongShoulders, healthy'), ('red', 'slow, weakknees, weak')]),
    ('school', [('green', 'inquisitive, teacher')]),
    ('research', [('green', 'strongShoulders, swift'), ('red', 'slow, weakknees')]),
    ('fishing', [('green', 'warmCore, swift, healthy')]),
    ('docks', [('green', 'strongShoulders, swift'), ('red', 'slow, weak')]),
]

def lines():
    out = ['[groups]'] + ['%s = %s' % g for g in GROUPS]
    for t, rules in TARGETS:
        out.append('[%s]' % t)
        out += ['%s = %s' % r for r in rules]
    return out

def base_string():
    return '|'.join(lines())

# Reference lists for the defaults file (comments only; not part of the built-in rules).
# Trait ids = the game's trait.<id> text keys; English names and effects from lang.csv (0.7.207).
TRAITS = [
    ('swift', 'Swift', '+15 move speed'),
    ('slow', 'Slow', 'walks slowly'),
    ('strongShoulders', 'Strong Shoulders', '+2 carry capacity'),
    ('weak', 'Weak', 'cannot lift much'),
    ('weakknees', 'Weak Knees', 'dislikes heavy labour, gets hurt more'),
    ('mascochist', 'Masochist', 'happy to do hard labour'),
    ('diligent', 'Diligent', 'works very hard'),
    ('mypace', 'My Pace', 'works at their own pace'),
    ('perfectionist', 'Perfectionist', 'cares about perfect execution'),
    ('unsafe', 'Unsafe worker', 'wears out machinery faster (unsafeworker also works)'),
    ('scientist', 'Sneaky', 'works faster at research'),
    ('teacher', 'Gifted Teacher', 'teaches others faster'),
    ('inquisitive', 'Inquisitive', 'learns faster at school'),
    ('lightEater', 'Light Eater', 'eats one less food per meal'),
    ('heavyEater', 'Heavy Eater', 'eats one more food per meal'),
    ('healthy', 'Healthy', 'resistant to illness and injury'),
    ('sickly', 'Sickly', 'less resistant to cold and illness'),
    ('warmCore', 'Warm Core', 'extra resistant to cold'),
    ('nosmell', "Can't Smell", 'no bad thoughts from pollution'),
    ('optimist', 'Optimist', 'positive thoughts can count double'),
    ('pessimist', 'Pessimist', 'negative thoughts can count double'),
    ('thoughtful', 'Thoughtful', 'more positive and negative thoughts'),
    ('content', 'Content', 'content with their circumstances'),
    ('greedy', 'Greedy', 'expects more from life'),
    ('patient', 'Patient', 'not in a rush'),
    ('compassionate', 'Compassionate', 'expects less, very sad when others die'),
    ('snorer', 'Snores', 'annoys others sleeping in the same home'),
    ('loner', 'Loner', 'unhappy working or living with others'),
    ('rude', 'Rude', 'can make passing whiskers unhappy'),
    ('considerate', 'Considerate', 'not offended by rude comments'),
    ('nosey', 'Nosey', 'sometimes asks rude questions'),
    ('rebellious', 'Rebellious', 'spreads rebellious talk'),
    ('monarchist', 'Monarchist', 'loyal to the Claws'),
]
# Building ids (class names without _C) with their English names, by default group.
BUILDINGS = [
    ('factory', [('Apothecary', 'Apothecary'), ('Bakery', 'Bakery'), ('Blacksmith', 'Blacksmith'),
                 ('BlastFurnace', 'Blast Furnace'), ('Brickmaker', 'Stone Cutter'), ('Cannery', 'Cannery'),
                 ('CannonFoundry', 'Cannon Foundry'), ('carpenter', 'Carpenter'), ('CoalSifter', 'Sifting Tower'),
                 ('CottonGin', 'Cotton Gin'), ('fineKitchen', 'Fine Kitchen'), ('fishery', 'Smokery'),
                 ('FlaxSpinner', 'Flax Spinner'), ('lumbermill', 'Sawmill'), ('Machinist', 'Machinist'),
                 ('mill', 'Mill'), ('netter', 'Netter'), ('OilPress', 'Oil Press'), ('OreSmelter', 'Ore Furnace'),
                 ('SailManufactory', 'Sail Manufactory'), ('SmallFurnace', 'Charcoal Furnace'),
                 ('SpiceGrinder', 'Spice Grinder'), ('stewery', 'Soup Kitchen'), ('Tailor', 'Tailor'),
                 ('Teaprocessor', 'Tea Roaster'), ('Toolmaker', 'Coppersmith'), ('Weaver', 'Weaver'),
                 ('SmallShipyard', 'Small Shipyard'), ('Shipyard', 'Large Shipyard'), ('GiantShipyard', 'Royal Shipyard')]),
    ('extraction', [('MiningCamp', 'Mining Camp'), ('WoodcuttersCamp', 'Woodcutter'), ('farm', 'Farm'),
                    ('Earthworks', 'Earthworks'), ('Gatherer', 'Forage Hut'), ('ConstructionYard', 'Construction Yard'),
                    ('LogisticsHub', 'Logistics Hub'), ('FireTender', 'Fire Tender')]),
    ('service', [('FoodVending', 'Cafe'), ('fancyVending', 'Dining Hall'), ('Supplier', 'Luxuries Supplier')]),
    ('office', [('CoordinationOffice', 'Management Office'), ('TriageBeds', 'Medical Triage')]),
    ('school', [('School', 'School')]),
    ('research', [('researchBuilding', 'Research Lab'), ('Laboratory', 'Laboratory')]),
    ('fishing', [('fishing_dock', 'Fishing Dock')]),
    ('docks', [('navaldock_scout', 'Exploration Dock'), ('navaldock_fishing', 'Deep Sea Fishing Dock'),
               ('navaldock_guano', 'Guano Collection Dock'), ('navaldock_trade', 'Trade Ship Dock'),
               ('navaldock_war', 'Naval Dock'), ('navaldock_hunting', 'Leviathan Hunting Berth')]),
    (None, [('Archive', 'Research Archive'), ('Bathhouse', 'Bathhouse'), ('CivicOffice', 'Civic Office'),
            ('DefensiveTower', 'Small Defensive Tower'), ('HangingGarden', 'Hanging Garden'),
            ('Incinerator', 'Incinerator'), ('Mousewheel', 'Whisker Wheel'), ('TerraformRig', 'Stone-Dump'),
            ('TownHall', 'Town Hall'), ('navaldock_storagePier', 'Storage Dock'), ('nauticalRaftDock', 'Ferry Dock'),
            ('raftDock', 'Raft Dock'), ('QuestRepairDock', 'Makeshift Repair Dock')]),
]

def _wrap(prefix, items, width=110):
    out, cur = [], prefix
    for it in items:
        add = it + ', '
        if len(cur) + len(add) > width and cur.strip() != ';':
            out.append(cur.rstrip(', ').rstrip()); cur = ';   '
        cur += add
    out.append(cur.rstrip(', '))
    return out

def reference():
    r = [';', '; ---------------------------------------------------------------------------',
         '; HOW TO USE',
         '; Sections: [all], [fuel] (the recipe burns fuel), [nofuel], a group name or a building id.',
         ';   [groups] defines groups:  mygroup = Bakery, stewery   (repeating a name adds buildings).',
         '; Keys: green, yellow, red, neutral (neutral removes the colour). Values: trait ids, comma-separated.',
         '; Upper/lower case and spaces do not matter. ; and # start a comment.',
         ';', '; ---------------------------------------------------------------------------',
         '; TRAIT IDS  (id = name in game: effect)']
    w = max(len(t[0]) for t in TRAITS)
    r += [';   %-*s = %s: %s' % (w, i, n, d) for i, n, d in TRAITS]
    r += [';', '; ---------------------------------------------------------------------------',
          '; BUILDING IDS  (id = name in game), by default group']
    w = max(len(b[0]) for _, bs in BUILDINGS for b in bs)
    for grp, bs in BUILDINGS:
        r.append(';' if grp else ';')
        r.append('; [%s]' % grp if grp else '; Not in any default group (only matters if the building has worker slots):')
        r += [';   %-*s = %s' % (w, i, n) for i, n in bs]
    r += [';', '; Not listed? Turn on debug logging (TraitPeekConfig\\debug.txt with any text);',
          '; the log then prints the id of every building window you open.',
          '; ---------------------------------------------------------------------------', '']
    return r

def ini_file():
    hdr = ['; TraitPeek built-in colour rules (for reference - these are inside the mod).',
           '; Your own rules: %localappdata%\\Whiskerwood\\Saved\\mods\\TraitPeekConfig\\TraitPeek.txt',
           '; They are read after these, top to bottom; a later line wins for the same trait.'] + reference()
    body = []
    for l in lines():
        if l.startswith('[') and body: body.append('')
        body.append(l)
    return '\n'.join(hdr + body) + '\n'
