"""Python mirror of the Blueprint rule logic (same string operations), for checking rules."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import traitpeek_rules as R
ALIASES = {'pessimest': 'pessimist', 'unsafeworker': 'unsafe'}

def parse(text):
    text = text.replace('\n', '|')   # '\r' stays, like in the game
    gnames, gmembers, rt, rc, rtr = [], [], [], [], []
    section = ''
    for line in [l for l in text.split('|') if l]:
        l0 = line.split('#', 1)[0] if '#' in line else line
        l0 = l0.split(';', 1)[0] if ';' in l0 else l0
        l = l0.lstrip().rstrip().replace(' ', '').lower()   # BP: Trim (leading) + TrimTrailing
        if not l: continue
        if l.startswith('['): section = l.replace('[', '').replace(']', ''); continue
        key, _, value = l.partition('=')
        if section == 'groups':
            if key in gnames:
                i = gnames.index(key); gmembers[i] = gmembers[i] + value + ','
            else:
                gnames.append(key); gmembers.append(',' + value + ',')
        else:
            rt.append(section); rc.append(key); rtr.append(value)
    return gnames, gmembers, rt, rc, rtr

def colours(rules, cls_display, polluting):
    gnames, gmembers, rt, rc, rtr = rules
    bid = (cls_display + '|').replace('_C|', '').replace('_c|', '').replace('|', '').lower()
    targets = ',all,' + bid + ','
    for n, m in zip(gnames, gmembers):
        if ',' + bid + ',' in m: targets += n + ','
    fuel = polluting or ',fuel,' in targets
    targets += 'fuel,' if fuel else 'nofuel,'
    lists = {'green': ',', 'yellow': ',', 'red': ','}
    for t, c, trs in zip(rt, rc, rtr):
        if ',' + t + ',' not in targets: continue
        for part in [p for p in trs.split(',') if p]:
            pt = part.lstrip().rstrip().lower(); tr = ALIASES.get(pt, pt)
            for k in lists: lists[k] = lists[k].replace(',' + tr + ',', ',')
            if c in lists: lists[c] += tr + ','
    return targets, lists

if __name__ == '__main__':
    rules = parse(R.base_string())
    for b, p in [('Bakery_C', True), ('Brickmaker_C', False), ('CoalSifter_C', False), ('MiningCamp_C', False),
                 ('fancyVending_C', False), ('CoordinationOffice_C', False), ('navaldock_trade_C', False), ('DefensiveTower_C', False)]:
        t, l = colours(rules, b, p); print(b, t, l)
    user = ("; my changes\r\n[groups]\r\nfactory  = DefensiveTower   ; adds\r\nkitchens = Bakery, stewery, fineKitchen\r\n"
            "[bakery]\r\ngreen   = swift\r\nneutral = rebellious\r\n[kitchens]\r\nred = sickly # comment\r\n")
    rules2 = parse(R.base_string() + '|' + user)
    for b, p in [('Bakery_C', True), ('DefensiveTower_C', False), ('stewery_C', True)]:
        t, l = colours(rules2, b, p); print('user', b, t, l)
