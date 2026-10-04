"""TraitPeek base rules, INI style. Built into WBP_TraitPeek as one string (lines joined with '|').
The user's %localappdata%\\Whiskerwood\\Saved\\mods\\TraitPeekConfig\\TraitPeek.ini is read after
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

def ini_file():
    hdr = ['; TraitPeek built-in colour rules (for reference - these are inside the mod).',
           '; Your own rules: %localappdata%\\Whiskerwood\\Saved\\mods\\TraitPeekConfig\\TraitPeek.ini',
           '; They are read after these, top to bottom; a later line wins for the same trait.', '']
    body = []
    for l in lines():
        if l.startswith('[') and body: body.append('')
        body.append(l)
    return '\n'.join(hdr + body) + '\n'
