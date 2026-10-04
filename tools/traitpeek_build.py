"""Generates the Blueprint paste text (T3D) for TraitPeek's graphs into tools/out/.
Usage: python tools/traitpeek_build.py   (needs the modkit's jmap, see t3d.py)
Paste each file into the matching asset's graph (Ctrl+A, Delete, Ctrl+V), compile.

How it works (1.0):
- BP_MapLoad (Actor): onLoadingFinished -> Debug (debug.txt), creates WBP_TraitLayer (an always-on,
  click-through canvas that holds the trait columns) and WBP_TraitPeek (the worker). Any key or mouse
  button released in the world (InputKey AnyKey, works while paused) "kicks" TraitPeek.
- Kick = add WBP_TraitPeek to the viewport (or restart its 0.4 s window if it is already there).
  While it is in the viewport its Tick refreshes every frame (UI ticks even while paused); after
  0.4 s it removes itself and nothing runs until the next kick. Clicks on the open window's own
  buttons (arrows, +/-, slots, picker, close) are bound to the same kick.
- Refresh: open building window = visible ArcoView whose Context is a GridActor. Workers come from the
  building's worker component (Industry, FarmBuilding, ... m_workers.m_workerSlots, in slot order);
  unknown building types fall back to "every whisker whose workplace is this building".
  Trait ids pessimest / unsafeworker are mapped to their text keys trait.pessimist / trait.unsafe.
  Each name label (string_name) claims the first unused column with that name, so two whiskers
  with the same name each get their own column.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from t3d import *

OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)
M = '/Game/Mods/TraitPeek/'
CHIP, ROW, PEEK, MAPLOAD = M + 'WBP_TraitChip', M + 'WBP_TraitRow', M + 'WBP_TraitPeek', M + 'BP_MapLoad'
COLUMN = M + 'WBP_TraitColumn'
KSL = '/Script/Engine.KismetSystemLibrary'
KML = '/Script/Engine.KismetMathLibrary'
KSTR = '/Script/Engine.KismetStringLibrary'
KTXT = '/Script/Engine.KismetTextLibrary'
API = '/Script/SystemCore.ModAPI'
AGENT = '/Script/ProjectArco.Prototype_Agent'
LC = STRUCT('/Script/CoreUObject.LinearColor')
V2 = STRUCT('/Script/CoreUObject.Vector2D')
GEO = STRUCT('/Script/SlateCore.Geometry')
VIS = ENUM('/Script/UMG.ESlateVisibility')

def modapi(g, x, y):
    return g.call(API + ':GetModAPI', 'Api', x, y)

class _Gate(Node):
    """Exec block 'if Debug: LogMessage', joined again by a reroute knot. Not a graph node itself."""
    def __init__(self, entry, exit_):
        self._e, self._x = entry, exit_; self.name = entry.node.name
    def __getitem__(self, k):
        return {'execute': self._e, 'then': self._x}[k]

def log(g, x, y, msg_pin=None, msg=None, name='Log'):
    """Debug-only log line: runs only when the Debug variable is true (debug.txt next to the pak)."""
    dg = g.get('Debug', BOOL, x - 200, y + 120, name=name + 'DebugGet')
    br = g.branch(x - 150, y, name + 'IfDebug'); link(dg['Debug'], br['Condition'])
    a = modapi(g, x, y + 160)
    n = g.call(API + ':LogMessage', name, x + 250, y, doPrependDate='true')
    link(a['ReturnValue'], n['self'])
    if msg_pin: link(msg_pin, n['Msg'])
    elif msg: n.set('Msg', msg)
    ex(br, n)
    k = g.add(BG + 'K2Node_Knot', name + 'Join', [], x + 500, y - 40)
    k.pin('InputPin', EXEC); k.pin('OutputPin', EXEC, out=True)
    link(n['then'], k['InputPin']); link(br['else'], k['InputPin'])
    return _Gate(br['execute'], k['OutputPin'])

def concat(g, x, y, *parts):
    """parts: Pin or str. returns output pin"""
    cur = None
    for i, p in enumerate(parts):
        if cur is None:
            if isinstance(p, str):
                c = g.call(KSTR + ':Concat_StrStr', 'Cat', x, y); c.set('A', p); cur = c['ReturnValue']; first = c; continue
            cur = p; continue
        c = g.call(KSTR + ':Concat_StrStr', 'Cat', x + 40 * i, y + 30 * i)
        link(cur, c['A'])
        if isinstance(p, str): c.set('B', p)
        else: link(p, c['B'])
        cur = c['ReturnValue']
    return cur

def is_valid(g, pin, x, y, name='Valid'):
    n = g.call(KSL + ':IsValid', name, x, y); link(pin, n['Object']); return n['ReturnValue']

# =========================================================================== CHIP
g = Graph(CHIP)
ev = g.custom_event('SetData', [('InText', STR), ('InColor', LC)], 0, 0)
lab = g.get('Label', OBJ('/Script/UMG.TextBlock'), 200, 200)
st = g.call('/Script/UMG.TextBlock:SetText', 'SetLabel', 450, 0)
tt = g.call(KTXT + ':Conv_StringToText', 'ToText', 200, 300)
link(ev['InText'], tt['InString']); link(tt['ReturnValue'], st['InText']); link(lab['Label'], st['self'])
bd = g.get('ChipBorder', OBJ('/Script/UMG.Border'), 500, 200)
sc = g.call('/Script/UMG.Border:SetContentColorAndOpacity', 'Tint', 800, 0)
link(bd['ChipBorder'], sc['self']); link(ev['InColor'], sc['InContentColorAndOpacity'])
ex(ev, st); ex(st, sc)
open(OUT + '/WBP_TraitChip.txt', 'w').write(g.text())

# =========================================================================== COLUMN
g = Graph(COLUMN)
ev = g.custom_event('SetData', [('InAgent', OBJ(AGENT)), ('InTable', NAME)], 0, 0)
ch = g.get('m_characteristics', STRUCT('/Script/ProjectArco.AgentCharacteristics'), 150, 250, owner=AGENT, name='Chars')
link(ev['InAgent'], ch['self'])
# break struct
props = J()['/Script/ProjectArco.AgentCharacteristics']['properties']
br = g.add(BG + 'K2Node_BreakStruct', 'BreakChars', ['StructType="/Script/CoreUObject.ScriptStruct\'/Script/ProjectArco.AgentCharacteristics\'"', 'bMadeAfterOverridePinRemoval=True'], 450, 250)
for i, p in enumerate(props):
    show = p['name'] in ('agentName', 'traits')
    br.header.append('ShowPinForProperties(%d)=(PropertyName="%s",bShowPin=%s,bCanToggleVisibility=True)' % (i, p['name'], show))
br.pin('AgentCharacteristics', STRUCT('/Script/ProjectArco.AgentCharacteristics'))
br.pin('agentName', STR, out=True)
br.pin('traits', SET(NAME), out=True)
link(ch['m_characteristics'], br['AgentCharacteristics'])

chips = g.get('Chips', OBJ('/Script/UMG.WrapBox'), 1150, 200)
clr = g.call('/Script/UMG.PanelWidget:ClearChildren', 'ClearChips', 1250, 0)
link(chips['Chips'], clr['self'])
toa = g.add(BG + 'K2Node_CallFunction', 'TraitsToArray',
            ['FunctionReference=(MemberParent="%s",MemberName="Set_ToArray")' % cls_ref('/Script/Engine.BlueprintSetLibrary')], 1500, 0)
toa.pin('execute', EXEC); toa.pin('then', EXEC, out=True)
toa.pin('self', OBJ('/Script/Engine.BlueprintSetLibrary'), defobj='/Script/Engine.Default__BlueprintSetLibrary', hidden=True, friendly='NSLOCTEXT("K2Node", "Target", "Target")')
sa = SET(NAME); sa['ref'] = True; sa['const'] = True
toa.pin('A', sa); toa.pin('Result', ARR(NAME), out=True)
link(br['traits'], toa['A'])
loop = g.macro('ForEachLoop', NAME, 1800, 0, name='TraitLoop')
link(toa['Result'], loop['Array'])
ex(ev, clr); ex(clr, toa); ex(toa, loop, 'then', 'Exec')

NEG = ',snorer,loner,heavyEater,pessimist,sickly,unsafe,rude,rebellious,weak,slow,weakknees,greedy,mypace,'
POS = ',lightEater,strongShoulders,swift,optimist,scientist,mascochist,healthy,warmCore,nosmell,diligent,teacher,considerate,inquisitive,content,'
rn = g.call(KSTR + ':Conv_NameToString', 'RowName', 2000, 300); link(loop['Array Element'], rn['InName'])
raw = g.call(KSTR + ':Replace', 'StripPrefix', 2250, 300, From='trait.', To='', SearchCase='IgnoreCase'); link(rn['ReturnValue'], raw['SourceString'])
# trait ids whose text key is spelled differently in the game's own code (0.7.207 exe strings)
ALIASES = [('pessimest', 'pessimist'), ('unsafeworker', 'unsafe')]
cur = raw['ReturnValue']
for i, (gid_, key_) in enumerate(ALIASES):
    eqa = g.call(KSTR + ':EqualEqual_StriStri', 'Is_' + gid_, 2250 + 250 * i, 150, B=gid_); link(cur, eqa['A'])
    sela = g.call(KML + ':SelectString', 'Alias_' + gid_, 2350 + 250 * i, 50, A=key_); link(cur, sela['B']); link(eqa['ReturnValue'], sela['bPickA'])
    cur = sela['ReturnValue']
bare = {'ReturnValue': cur}
key = concat(g, 2500, 300, 'trait.', bare['ReturnValue'])
kn = g.call(KSTR + ':Conv_StringToName', 'KeyAsName', 2750, 300); link(key, kn['InString'])
hk = g.call('/Script/SystemCore.LocManager:HasKey', 'HasLocKey', 3000, 300); link(kn['ReturnValue'], hk['Key'])
wk = g.call('/Script/SystemCore.LocManager:GetWordFromKey', 'LocWord', 3000, 420); link(kn['ReturnValue'], wk['Key'])
s2 = g.call(KML + ':SelectString', 'PickDisp', 3250, 300)
link(wk['ReturnValue'], s2['A']); link(bare['ReturnValue'], s2['B']); link(hk['ReturnValue'], s2['bPickA'])
wrapped = concat(g, 2500, 700, ',', bare['ReturnValue'], ',')
neg = g.call(KSTR + ':Contains', 'IsNegative', 2850, 700, SearchIn=NEG); link(wrapped, neg['Substring'])
pos = g.call(KSTR + ':Contains', 'IsPositive', 2850, 850, SearchIn=POS); link(wrapped, pos['Substring'])
c1 = g.call(KML + ':SelectColor', 'PosOrNeutral', 3150, 850,
            A='(R=0.550000,G=0.950000,B=0.500000,A=1.000000)', B='(R=0.900000,G=0.850000,B=0.700000,A=1.000000)')
link(pos['ReturnValue'], c1['bPickA'])
c2 = g.call(KML + ':SelectColor', 'TraitColor', 3450, 700, A='(R=1.000000,G=0.450000,B=0.400000,A=1.000000)')
link(c1['ReturnValue'], c2['B']); link(neg['ReturnValue'], c2['bPickA'])
cw = g.create_widget(CHIP, 2850, 0, name='CreateChip')
ex(loop, cw, 'LoopBody')
sd = g.bpcall(CHIP, 'SetData', [('InText', STR), ('InColor', LC)], name='ChipSetData', x=3450, y=0)
link(cw['ReturnValue'], sd['self']); link(s2['ReturnValue'], sd['InText']); link(c2['ReturnValue'], sd['InColor'])
ex(cw, sd)
chips2 = g.get('Chips', OBJ('/Script/UMG.WrapBox'), 3700, 200)
ac = g.call('/Script/UMG.PanelWidget:AddChild', 'AddChip', 3800, 0)
link(chips2['Chips'], ac['self']); link(cw['ReturnValue'], ac['Content'])
ex(sd, ac)
open(OUT + '/WBP_TraitColumn.txt', 'w').write(g.text())

# =========================================================================== PEEK
# WBP_TraitPeek (Widget BP, parent UserWidget). Designer: Canvas Root, Not Hit-Testable (Self Only).
g = Graph(PEEK)
PEEK_CLS = "/Script/UMG.WidgetBlueprintGeneratedClass'%s.%s_C'" % (PEEK, PEEK.split('/')[-1])
WIDGET = OBJ('/Script/UMG.Widget'); ACTOR = OBJ('/Script/Engine.Actor'); AG = OBJ(AGENT)
COLT = T('object', obj=bp_cls_ref(COLUMN))
VIEW = OBJ('/Script/ProjectArco.ArcoView')
CANVAS = OBJ('/Script/UMG.CanvasPanel')
NAVI = '/Script/SystemCore.NaviUi'
PA = '/Script/ProjectArco.'
WSLOT = STRUCT(PA + 'WorkerSlot'); WASSIGN = STRUCT(PA + 'WorkerAssignment')
WORKER_COMPONENTS = ['Industry', 'FarmBuilding', 'HarvestingCamp', 'ResourceBuilding', 'School', 'ResearchLab',
    'LogisticsHub', 'FoodDistributor', 'ConstructionYard', 'ConsumptionOffice', 'CoordinationOffice',
    'DefensiveTower', 'JobTicketDispenserBuilding', 'PackageDelivery', 'TaxOffice', 'TerraformBuilding',
    'TerraformCamp', 'TradePort', 'TriageBuilding', 'WorkDock']
WINDOW = '0.4'   # seconds of per-frame refreshes after each kick


def bind_self(g, target_pin, owner, delegate, sig_pkg, sig, event_node, x, y, name):
    n = g.add(BG + 'K2Node_AddDelegate', name,
              ['DelegateReference=(MemberParent="%s",MemberName="%s")' % (cls_ref(owner), delegate)], x, y)
    n.pin('execute', EXEC); n.pin('then', EXEC, out=True)
    n.pin('self', OBJ(owner), friendly='NSLOCTEXT("K2Node", "Target", "Target")')
    d = n.pin('Delegate', T('delegate'))
    d.memref = 'MemberParent="/Script/CoreUObject.Package\'%s\'",MemberName="%s"' % (sig_pkg, sig)
    link(target_pin, n['self'])
    ev = event_node['OutputDelegate']
    ev.memref = 'MemberParent="%s",MemberName="%s"' % (PEEK_CLS, event_node.name)
    link(ev, d)
    return n


def class_array(g, cls, x, y, name='Classes'):
    n = g.add(BG + 'K2Node_MakeArray', name, ['NumInputs=1'], x, y)
    ct = T('class', obj=cls_ref('/Script/CoreUObject.Object'))
    n.pin('Array', ARR(ct), out=True)
    n.pin('[0]', ct, defobj=cls)
    return n

def array_get(g, elem_t, x, y, name='Get'):
    n = g.add(BG + 'K2Node_GetArrayItem', name, [], x, y)
    at = ARR(elem_t); at['ref'] = True
    n.pin('Array', at); n.pin('Dimension 1', INT, default='0'); n.pin('Output', elem_t, out=True)
    return n

def array_find(g, elem_t, x, y, name='Find'):
    n = g.add(BG + 'K2Node_CallArrayFunction', name, ['bDefaultsToPureFunc=True',
        'FunctionReference=(MemberParent="%s",MemberName="Array_Find")' % cls_ref('/Script/Engine.KismetArrayLibrary')], x, y)
    n.pin('self', OBJ('/Script/Engine.KismetArrayLibrary'), defobj='/Script/Engine.Default__KismetArrayLibrary', hidden=True, friendly='NSLOCTEXT("K2Node", "Target", "Target")')
    at = ARR(elem_t); at['ref'] = True; at['const'] = True
    it = dict(elem_t); it['ref'] = True; it['const'] = True
    n.pin('TargetArray', at); n.pin('ItemToFind', it); n.pin('ReturnValue', INT, out=True)
    return n

def array_set(g, elem_t, x, y, name='ArraySet'):
    n = g.add(BG + 'K2Node_CallArrayFunction', name,
        ['FunctionReference=(MemberParent="%s",MemberName="Array_Set")' % cls_ref('/Script/Engine.KismetArrayLibrary')], x, y)
    n.pin('execute', EXEC); n.pin('then', EXEC, out=True)
    n.pin('self', OBJ('/Script/Engine.KismetArrayLibrary'), defobj='/Script/Engine.Default__KismetArrayLibrary', hidden=True, friendly='NSLOCTEXT("K2Node", "Target", "Target")')
    at = ARR(elem_t); at['ref'] = True
    it = dict(elem_t); it['ref'] = True; it['const'] = True
    n.pin('TargetArray', at); n.pin('Index', INT, default='0'); n.pin('Item', it); n.pin('bSizeToFit', BOOL, default='false')
    return n

def struct_break(g, spath, show, x, y, name):
    props = J()[spath]['properties']
    n = g.add(BG + 'K2Node_BreakStruct', name, ['StructType="/Script/CoreUObject.ScriptStruct\'%s\'"' % spath, 'bMadeAfterOverridePinRemoval=True'], x, y)
    for i, p in enumerate(props):
        n.header.append('ShowPinForProperties(%d)=(PropertyName="%s",bShowPin=%s,bCanToggleVisibility=True)' % (i, p['name'], p['name'] in show))
    n.pin(spath.split('.')[-1], STRUCT(spath))
    for p in props:
        if p['name'] in show: n.pin(p['name'], prop_type(p), out=True)
    return n

def cast_np(g, target, x, y, name):
    """impure cast; output pin renamed to As<ClassName> without spaces"""
    c = g.cast(target, False, x, y, name=name)
    for p in c.pins:
        if p.name.startswith('As'): p.name = p.name.replace(' ', '')
    return c

def remove_columns(g, x, y, suffix):
    """ForEach Columns -> RemoveFromParent; then clear Columns, ColNames. returns (first, last)"""
    cg = g.get('Columns', ARR(COLT), x, y + 250, name='ColumnsRm' + suffix)
    lp = g.macro('ForEachLoop', COLT, x + 200, y, name='RemoveLoop' + suffix); link(cg['Columns'], lp['Array'])
    rf = g.call('/Script/UMG.Widget:RemoveFromParent', 'RemoveCol' + suffix, x + 500, y); link(lp['Array Element'], rf['self'])
    ex(lp, rf, 'LoopBody')
    cg2 = g.get('Columns', ARR(COLT), x + 500, y + 350, name='ColumnsClr' + suffix)
    c1 = g.arr('Array_Clear', COLT, x + 700, y + 200, name='ClearColumns' + suffix); link(cg2['Columns'], c1['TargetArray'])
    ex(lp, c1, 'Completed')
    ng = g.get('ColNames', ARR(STR), x + 700, y + 450, name='ColNamesClr' + suffix)
    c2 = g.arr('Array_Clear', STR, x + 950, y + 200, name='ClearColNames' + suffix); link(ng['ColNames'], c2['TargetArray'])
    ex(c1, c2)
    return lp, c2

# ---- Construct (every time the worker is added to the viewport): restart the window, rebind buttons
con = g.event('/Script/UMG.UserWidget', 'Construct', [], 'Construct', 0, -2400)
sw0 = g.setv('Waited', DBL, 300, -2400, value='0.0', name='StartWindow'); ex(con, sw0)
sbf = g.setv('Bound', BOOL, 550, -2400, value='false', name='RebindButtons'); ex(sw0, sbf)

# ---- Kick: a button in the open window was clicked (or the picker is open): keep / start the window
evU = g.custom_event('OnUiClick', [], 0, -2000)
sbf2 = g.setv('Bound', BOOL, 250, -2000, value='false', name='RebindAfterClick'); ex(evU, sbf2)
inv = g.call('/Script/UMG.Widget:IsInViewport', 'Running', 500, -1850)
bk = g.branch(500, -2000, 'BrRunning'); link(inv['ReturnValue'], bk['Condition']); ex(sbf2, bk)
swr = g.setv('Waited', DBL, 750, -2050, value='0.0', name='RestartWindow'); ex(bk, swr)
atv = g.call('/Script/UMG.UserWidget:AddToViewport', 'StartRunning', 750, -1900, ZOrder='6'); ex(bk, atv, 'else')

# ---- Tick (only while in the viewport, i.e. for 0.4 s after a kick): refresh every frame
tk = g.event('/Script/UMG.UserWidget', 'Tick', [('MyGeometry', GEO), ('InDeltaTime', FLT)], 'Tick', 0, 0)
wg = g.get('Waited', DBL, 0, 250, name='WaitedGet')
add = g.call(KML + ':Add_DoubleDouble', 'WaitedAdd', 200, 250); link(wg['Waited'], add['A']); link(tk['InDeltaTime'], add['B'])
sa = g.setv('Waited', DBL, 300, 0, name='SetWaited'); link(add['ReturnValue'], sa['Waited']); ex(tk, sa)
ge = g.call(KML + ':GreaterEqual_DoubleDouble', 'WindowOver', 500, 250, B=WINDOW); link(sa['Output_Get'], ge['A'])
bdue = g.branch(550, 0, 'BrWindowOver'); link(ge['ReturnValue'], bdue['Condition']); ex(sa, bdue)
stop = g.call('/Script/UMG.Widget:RemoveFromParent', 'StopRunning', 800, -150); ex(bdue, stop)
# refresh starts here (both after StopRunning and directly)
srw = g.setv('Waited', DBL, 1000, -150, value='0.0', name='ResetWaited'); ex(stop, srw)
srb = g.setv('Bound', BOOL, 1000, -300, value='false', name='ResetBound'); ex(srw, srb)
san = g.setv('Anchor', WIDGET, 1200, 0, name='ClearAnchor'); ex(bdue, san, 'else'); ex(srb, san)
sbn = g.setv('Building', ACTOR, 1450, 0, name='ClearBuilding'); ex(san, sbn)
gw = g.call('/Script/UMG.WidgetBlueprintLibrary:GetAllWidgetsOfClass', 'FindViews', 1700, 0,
            WidgetClass='/Script/ProjectArco.ArcoView', TopLevelOnly='false')
gw['FoundWidgets'].t = ARR(VIEW)
ex(sbn, gw)
pl = g.macro('ForEachLoop', VIEW, 2050, 0, name='ViewLoop')
link(gw['FoundWidgets'], pl['Array']); ex(gw, pl, 'then', 'Exec')
cx = g.get('Context', ACTOR, 2100, 300, owner='/Script/ProjectArco.ArcoWidgetBase', name='ViewContext')
link(pl['Array Element'], cx['self'])
cxc = g.call('/Script/Engine.GameplayStatics:GetObjectClass', 'CtxClass', 2300, 400); link(cx['Context'], cxc['Object'])
isGrid = g.call(KML + ':ClassIsChildOf', 'CtxIsBuilding', 2500, 400, ParentClass='/Script/ProjectArco.GridActor'); link(cxc['ReturnValue'], isGrid['TestClass'])
okc = g.call(KML + ':BooleanAND', 'ViewOK', 2700, 300); link(is_valid(g, cx['Context'], 2300, 300), okc['A']); link(isGrid['ReturnValue'], okc['B'])
vis = g.call('/Script/UMG.Widget:IsVisible', 'ViewVisible', 2500, 550); link(pl['Array Element'], vis['self'])
okv = g.call(KML + ':BooleanAND', 'ViewShown', 2900, 400); link(okc['ReturnValue'], okv['A']); link(vis['ReturnValue'], okv['B'])
bok = g.branch(2400, 0, 'BrViewOK'); link(okv['ReturnValue'], bok['Condition']); ex(pl, bok, 'LoopBody')
sanc = g.setv('Anchor', WIDGET, 2700, 0, name='SetAnchor'); link(pl['Array Element'], sanc['Anchor']); ex(bok, sanc)
sbld = g.setv('Building', ACTOR, 2950, 0, name='SetBuilding'); link(cx['Context'], sbld['Building']); ex(sanc, sbld)

# ---- no building window open: remove columns
Y = 1000
ang = g.get('Anchor', WIDGET, 2100, Y + 250, name='AnchorGet')
bany = g.branch(2400, Y, 'BrFound'); link(is_valid(g, ang['Anchor'], 2250, Y + 250), bany['Condition']); ex(pl, bany, 'Completed')
rl0, rl0end = remove_columns(g, 2700, Y + 600, 'A'); ex(bany, rl0, 'else', 'Exec')
slk = g.setv('LastKey', STR, 4000, Y + 800, value='', name='ForgetKey'); ex(rl0end, slk)

# ---- window open: bind its buttons once per kick (clicks on game UI don't reach InputKey)
bbd = g.get('Bound', BOOL, 2600, Y - 250, name='BoundGet')
bbr = g.branch(2650, Y - 400, 'BrBound'); link(bbd['Bound'], bbr['Condition']); ex(bany, bbr)
fdb = g.call(NAVI + ':FindDecendentsOfClasses', 'WindowButtons', 2900, Y - 400, ignoreHidden='false')
link(g.get('Anchor', WIDGET, 2750, Y - 200, name='AnchorButtons')['Anchor'], fdb['searchRoot'])
link(class_array(g, '/Script/UMG.Button', 2750, Y - 100, name='ButtonClass')['Array'], fdb['candidateClasses'])
fdb['ReturnValue'].t = ARR(WIDGET)
ex(bbr, fdb, 'else')
blp = g.macro('ForEachLoop', WIDGET, 3200, Y - 400, name='ButtonLoop'); link(fdb['ReturnValue'], blp['Array']); ex(fdb, blp, 'then', 'Exec')
cbt = cast_np(g, '/Script/UMG.Button', 3450, Y - 400, 'AsButton'); link(blp['Array Element'], cbt['Object']); ex(blp, cbt, 'LoopBody')
bnd = bind_self(g, cbt['AsButton'], '/Script/UMG.Button', 'OnClicked', '/Script/UMG', 'OnButtonClickedEvent__DelegateSignature', evU, 3700, Y - 400, 'BindWindowButton')
ex(cbt, bnd)
sbt = g.setv('Bound', BOOL, 3500, Y - 600, value='true', name='SetBound'); ex(blp, sbt, 'Completed')

# ---- collect workers in slot order from the building's worker component
wgc = g.get('Workers', ARR(AG), 2900, Y + 250, name='WorkersClr')
clw = g.arr('Array_Clear', AG, 3000, Y, name='ClearWorkers'); link(wgc['Workers'], clw['TargetArray'])
ex(bbr, clw); ex(sbt, clw)
bg = g.get('Building', ACTOR, 3200, Y + 250, name='BuildingKey')
dn = g.call(KSL + ':GetDisplayName', 'BuildingName', 3400, Y + 250); link(bg['Building'], dn['Object'])
sk = g.setv('Key', STR, 3300, Y, name='StartKey'); link(dn['ReturnValue'], sk['Key']); ex(clw, sk)

SLOT_X = 3600 + 450 * len(WORKER_COMPONENTS) + 400
slotloop = g.macro('ForEachLoop', WSLOT, SLOT_X + 300, Y, name='SlotLoop')
link(g.get('Slots', ARR(WSLOT), SLOT_X + 100, Y + 250, name='SlotsLoopGet')['Slots'], slotloop['Array'])
prev = (sk, 'then')
for i, c in enumerate(WORKER_COMPONENTS):
    x = 3600 + 450 * i; yy = Y + 1600
    bgc = g.get('Building', ACTOR, x - 150, yy + 250, name='BuildingComp%d' % i)
    gc = g.call('/Script/Engine.Actor:GetComponentByClass', 'Find' + c, x - 100, yy + 350, ComponentClass=PA + c)
    link(bgc['Building'], gc['self'])
    cc = cast_np(g, PA + c, x, yy, 'As' + c); link(gc['ReturnValue'], cc['Object']); ex(prev[0], cc, prev[1])
    mw = g.get('m_workers', WASSIGN, x + 150, yy + 200, owner=PA + c, name='Workers' + c); link(cc['As' + c], mw['self'])
    br = struct_break(g, PA + 'WorkerAssignment', ['m_workerSlots'], x + 150, yy + 300, 'BreakWorkers' + c)
    link(mw['m_workers'], br['WorkerAssignment'])
    ss = g.setv('Slots', ARR(WSLOT), x + 250, yy - 250, name='Slots' + c); link(br['m_workerSlots'], ss['Slots']); ex(cc, ss)
    so = g.setv('Source', STR, x + 250, yy - 450, value=c, name='Source' + c); ex(ss, so)
    ex(so, slotloop, 'then', 'Exec')
    prev = (cc, 'CastFailed')
# slot -> agent
bsl = struct_break(g, PA + 'WorkerSlot', ['Agent'], SLOT_X + 550, Y + 250, 'BreakSlot'); link(slotloop['Array Element'], bsl['WorkerSlot'])
bhas = g.branch(SLOT_X + 600, Y, 'BrSlotFilled'); link(is_valid(g, bsl['Agent'], SLOT_X + 750, Y + 300, name='SlotHasAgent'), bhas['Condition'])
ex(slotloop, bhas, 'LoopBody')

def add_worker(g, agent_pin, x, y, sfx):
    wg2 = g.get('Workers', ARR(AG), x + 100, y + 200, name='WorkersAdd' + sfx)
    aw = g.arr('Array_Add', AG, x + 200, y, name='AddWorker' + sfx); link(wg2['Workers'], aw['TargetArray']); link(agent_pin, aw['NewItem'])
    kg = g.get('Key', STR, x + 400, y + 250, name='KeyGet' + sfx)
    wdn = g.call(KSL + ':GetDisplayName', 'WhiskerName' + sfx, x + 400, y + 350); link(agent_pin, wdn['Object'])
    kc = concat(g, x + 600, y + 250, kg['Key'], wdn['ReturnValue'])
    sk2 = g.setv('Key', STR, x + 500, y, name='GrowKey' + sfx); link(kc, sk2['Key']); ex(aw, sk2)
    return aw, sk2
awS, _ = add_worker(g, bsl['Agent'], SLOT_X + 850, Y, 'S'); ex(bhas, awS)

# fallback for building types without a known worker component: whiskers whose workplace is this building
FX = 3600 + 450 * len(WORKER_COMPONENTS); FY = Y + 2600
sof = g.setv('Source', STR, FX, FY, value='scan', name='SourceScan'); ex(prev[0], sof, prev[1])
gaa = g.call('/Script/Engine.GameplayStatics:GetAllActorsOfClass', 'AllWhiskers', FX + 250, FY, ActorClass=AGENT)
gaa['OutActors'].t = ARR(AG); ex(sof, gaa)
al = g.macro('ForEachLoop', AG, FX + 550, FY, name='WhiskerLoop'); link(gaa['OutActors'], al['Array']); ex(gaa, al, 'then', 'Exec')
wp = g.call('/Script/ProjectArco.Prototype_Agent:GetWorkplace', 'Workplace', FX + 750, FY + 300); link(al['Array Element'], wp['self'])
bg2 = g.get('Building', ACTOR, FX + 750, FY + 420, name='BuildingCmp')
eq = g.call(KML + ':EqualEqual_ObjectObject', 'WorksHere', FX + 1000, FY + 300); link(wp['ReturnValue'], eq['A']); link(bg2['Building'], eq['B'])
bwh = g.branch(FX + 950, FY, 'BrWorksHere'); link(eq['ReturnValue'], bwh['Condition']); ex(al, bwh, 'LoopBody')
awF, _ = add_worker(g, al['Array Element'], FX + 1200, FY, 'F'); ex(bwh, awF)

# ---- rebuild columns if the worker list changed
Y = 5000
kg2 = g.get('Key', STR, 3700, Y + 250, name='KeyCmp'); lkg = g.get('LastKey', STR, 3700, Y + 350, name='LastKeyCmp')
same = g.call(KSTR + ':EqualEqual_StrStr', 'SameKey', 3900, Y + 250); link(kg2['Key'], same['A']); link(lkg['LastKey'], same['B'])
bsame = g.branch(3900, Y, 'BrSame'); link(same['ReturnValue'], bsame['Condition'])
ex(slotloop, bsame, 'Completed'); ex(al, bsame, 'Completed')
slk2 = g.setv('LastKey', STR, 4150, Y + 150, name='RememberKey'); link(kg2['Key'], slk2['LastKey']); ex(bsame, slk2, 'else')
rl1, rl1end = remove_columns(g, 4400, Y + 150, 'B'); ex(slk2, rl1, 'then', 'Exec')
wg3 = g.get('Workers', ARR(AG), 5400, Y + 400, name='WorkersLoop')
cl = g.macro('ForEachLoop', AG, 5600, Y + 150, name='ColumnLoop'); link(wg3['Workers'], cl['Array']); ex(rl1end, cl, 'then', 'Exec')
ccw = g.create_widget(COLUMN, 5900, Y + 150, name='CreateColumn'); ex(cl, ccw, 'LoopBody')
csd = g.bpcall(COLUMN, 'SetData', [('InAgent', AG), ('InTable', NAME)], name='ColumnSetData', x=6200, y=Y + 150)
link(ccw['ReturnValue'], csd['self']); link(cl['Array Element'], csd['InAgent']); ex(ccw, csd)
rootg = g.get('LayerRoot', CANVAS, 6300, Y + 450, name='LayerRootGet')
addc = g.call('/Script/UMG.CanvasPanel:AddChildToCanvas', 'AddToLayer', 6500, Y + 150); link(rootg['LayerRoot'], addc['self']); link(ccw['ReturnValue'], addc['Content']); ex(csd, addc)
sas = g.call('/Script/UMG.CanvasPanelSlot:SetAutoSize', 'ColAutoSize', 6800, Y + 150, InbAutoSize='true'); link(addc['ReturnValue'], sas['self']); ex(addc, sas)
sal = g.call('/Script/UMG.CanvasPanelSlot:SetAlignment', 'ColAlign', 7050, Y + 150, InAlignment='(X=0.500000,Y=0.000000)'); link(addc['ReturnValue'], sal['self']); ex(sas, sal)
hid = g.call('/Script/UMG.Widget:SetVisibility', 'ColHidden', 7300, Y + 150, InVisibility='Collapsed'); link(ccw['ReturnValue'], hid['self']); ex(sal, hid)
cg = g.get('Columns', ARR(COLT), 7400, Y + 450, name='ColumnsAdd')
acol = g.arr('Array_Add', COLT, 7550, Y + 150, name='AddColumn'); link(cg['Columns'], acol['TargetArray']); link(ccw['ReturnValue'], acol['NewItem']); ex(hid, acol)
chs = g.get('m_characteristics', STRUCT('/Script/ProjectArco.AgentCharacteristics'), 7400, Y + 600, owner=AGENT, name='WorkerChars')
link(cl['Array Element'], chs['self'])
brw = struct_break(g, '/Script/ProjectArco.AgentCharacteristics', ['agentName'], 7650, Y + 600, 'BreakWorker')
link(chs['m_characteristics'], brw['AgentCharacteristics'])
ng = g.get('ColNames', ARR(STR), 7700, Y + 450, name='ColNamesAdd')
aname = g.arr('Array_Add', STR, 7850, Y + 150, name='AddColName'); link(ng['ColNames'], aname['TargetArray']); link(brw['agentName'], aname['NewItem']); ex(acol, aname)

# ---- place columns under the matching portraits
Y = 6400
src = g.get('Source', STR, 4000, Y + 250, name='SourceDbg')
sdb = g.setv('Dbg', STR, 4200, Y, name='ResetDbg'); link(concat(g, 4000, Y + 150, 'via ', src['Source'], ':'), sdb['Dbg'])
ex(bsame, sdb); ex(cl, sdb, 'Completed')
spn = g.setv('PassNames', ARR(STR), 4450, Y, name='CopyNames'); link(g.get('ColNames', ARR(STR), 4300, Y + 200, name='ColNamesCopy')['ColNames'], spn['PassNames']); ex(sdb, spn)
# hide every column first; the ones that find their label are shown again below
cgh = g.get('Columns', ARR(COLT), 4600, Y + 200, name='ColumnsHide')
hl = g.macro('ForEachLoop', COLT, 4700, Y, name='HideLoop'); link(cgh['Columns'], hl['Array']); ex(spn, hl, 'then', 'Exec')
hc = g.call('/Script/UMG.Widget:SetVisibility', 'HideColumn', 5000, Y - 150, InVisibility='Collapsed'); link(hl['Array Element'], hc['self']); ex(hl, hc, 'LoopBody')
# whisker picker open: keep everything hidden and keep refreshing until it closes
WAP = '/Script/ProjectArco.WorkerAssignmentPanel'
fpn = g.call(NAVI + ':FindDecendentsOfClasses', 'FindPanel', 5100, Y, ignoreHidden='false')
link(g.get('Anchor', WIDGET, 4950, Y + 200, name='AnchorPanel')['Anchor'], fpn['searchRoot'])
link(class_array(g, WAP, 4950, Y + 300, name='PanelClass')['Array'], fpn['candidateClasses']); ex(hl, fpn, 'Completed')
p0 = array_get(g, WIDGET, 5350, Y + 200, name='FirstPanel'); link(fpn['ReturnValue'], p0['Array'])
cwp = cast_np(g, WAP, 5400, Y, 'AsPanel'); link(p0['Output'], cwp['Object']); ex(fpn, cwp)
sel = g.get('m_isAgentSelectOpen', BOOL, 5650, Y + 200, owner=WAP, name='PickerOpen'); link(cwp['AsWorkerAssignmentPanel'], sel['self'])
bpk = g.branch(5700, Y, 'BrPickerOpen'); link(sel['m_isAgentSelectOpen'], bpk['Condition']); ex(cwp, bpk)
inv2 = g.call('/Script/UMG.Widget:IsInViewport', 'RunningPicker', 5950, Y - 150)
bk2 = g.branch(5950, Y - 300, 'BrRunningPicker'); link(inv2['ReturnValue'], bk2['Condition']); ex(bpk, bk2)
swr2 = g.setv('Waited', DBL, 6200, Y - 350, value='0.0', name='HoldWindow'); ex(bk2, swr2)
atv2 = g.call('/Script/UMG.UserWidget:AddToViewport', 'KeepRunning', 6200, Y - 200, ZOrder='6'); ex(bk2, atv2, 'else')

tbc = class_array(g, '/Script/UMG.TextBlock', 5900, Y + 450, name='TextBlockClass')
fd = g.call(NAVI + ':FindDecendentsOfClasses', 'FindTexts', 6000, Y + 150, ignoreHidden='true')
link(g.get('Anchor', WIDGET, 5900, Y + 350, name='AnchorSearch')['Anchor'], fd['searchRoot']); link(tbc['Array'], fd['candidateClasses'])
ex(bpk, fd, 'else'); ex(cwp, fd, 'CastFailed')
X0 = 6400; Y += 150
tl = g.macro('ForEachLoop', WIDGET, X0, Y, name='TextLoop'); link(fd['ReturnValue'], tl['Array']); ex(fd, tl, 'then', 'Exec')
wn = g.call(KSL + ':GetDisplayName', 'TextWidgetName', X0 + 150, Y + 300); link(tl['Array Element'], wn['Object'])
isn = g.call(KSTR + ':EqualEqual_StrStr', 'IsNameLabel', X0 + 350, Y + 300, B='string_name'); link(wn['ReturnValue'], isn['A'])
bnl = g.branch(X0 + 300, Y, 'BrNameLabel'); link(isn['ReturnValue'], bnl['Condition']); ex(tl, bnl, 'LoopBody')
ctb = cast_np(g, '/Script/UMG.TextBlock', X0 + 550, Y, 'AsTextBlock'); link(tl['Array Element'], ctb['Object']); ex(bnl, ctb)
gtx = g.call('/Script/UMG.TextBlock:GetText', 'LabelText', X0 + 700, Y + 450); link(ctb['AsTextBlock'], gtx['self'])
t2s = g.call(KTXT + ':Conv_TextToString', 'LabelString', X0 + 950, Y + 450); link(gtx['ReturnValue'], t2s['InText'])
pn = g.get('PassNames', ARR(STR), X0 + 1150, Y + 600, name='PassNamesFind')
fnd = array_find(g, STR, X0 + 1350, Y + 500, name='FindColumn'); link(pn['PassNames'], fnd['TargetArray']); link(t2s['ReturnValue'], fnd['ItemToFind'])
idxs = g.call(KSTR + ':Conv_IntToString', 'IdxStr', X0 + 1550, Y + 150); link(fnd['ReturnValue'], idxs['inInt'])
dbg = g.get('Dbg', STR, X0 + 950, Y + 250, name='DbgGrow')
sdb2 = g.setv('Dbg', STR, X0 + 800, Y, name='AddDbgName')
link(concat(g, X0 + 1150, Y + 250, dbg['Dbg'], ' ', t2s['ReturnValue'], '=', idxs['ReturnValue']), sdb2['Dbg']); ex(ctb, sdb2)
ge0 = g.call(KML + ':GreaterEqual_IntInt', 'HasColumn', X0 + 1600, Y + 500, B='0'); link(fnd['ReturnValue'], ge0['A'])
bhc = g.branch(X0 + 1100, Y, 'BrHasColumn'); link(ge0['ReturnValue'], bhc['Condition']); ex(sdb2, bhc)
# column = label's bottom-centre + (0, 88), in the layer's coordinates
lgeo = g.call('/Script/UMG.Widget:GetCachedGeometry', 'LayerGeo', X0 + 2600, Y + 450)
link(g.get('LayerRoot', CANVAS, X0 + 2450, Y + 550, name='LayerRootGeo')['LayerRoot'], lgeo['self'])
pgeo = g.call('/Script/UMG.Widget:GetCachedGeometry', 'PortraitGeo', X0 + 1450, Y + 250); link(tl['Array Element'], pgeo['self'])
psz = g.call('/Script/UMG.SlateBlueprintLibrary:GetLocalSize', 'PortraitSize', X0 + 1700, Y + 350); link(pgeo['ReturnValue'], psz['Geometry'])
pbk = g.call(KML + ':BreakVector2D', 'PortraitWH', X0 + 1900, Y + 350); link(psz['ReturnValue'], pbk['InVec'])
half = g.call(KML + ':Multiply_DoubleDouble', 'HalfWidth', X0 + 2100, Y + 300, B='0.5'); link(pbk['X'], half['A'])
bot = g.call(KML + ':MakeVector2D', 'BottomCenter', X0 + 2300, Y + 350); link(half['ReturnValue'], bot['X']); link(pbk['Y'], bot['Y'])
pabs = g.call('/Script/UMG.SlateBlueprintLibrary:LocalToAbsolute', 'PortraitAbs', X0 + 2500, Y + 300); link(pgeo['ReturnValue'], pabs['Geometry']); link(bot['ReturnValue'], pabs['LocalCoordinate'])
ploc = g.call('/Script/UMG.SlateBlueprintLibrary:AbsoluteToLocal', 'PortraitLocal', X0 + 2750, Y + 300); link(lgeo['ReturnValue'], ploc['Geometry']); link(pabs['ReturnValue'], ploc['AbsoluteCoordinate'])
poff = g.call(KML + ':Add_Vector2DVector2D', 'NudgeDown', X0 + 3000, Y + 300, B='(X=0.000000,Y=88.000000)'); link(ploc['ReturnValue'], poff['A'])
cg3 = g.get('Columns', ARR(COLT), X0 + 1450, Y + 700, name='ColumnsGet')
gcol = array_get(g, COLT, X0 + 1700, Y + 700, name='ColumnForName'); link(cg3['Columns'], gcol['Array']); link(fnd['ReturnValue'], gcol['Dimension 1'])
cslot = g.call('/Script/UMG.WidgetLayoutLibrary:SlotAsCanvasSlot', 'ColumnSlot', X0 + 1950, Y + 700); link(gcol['Output'], cslot['Widget'])
setp = g.call('/Script/UMG.CanvasPanelSlot:SetPosition', 'PlaceColumn', X0 + 3250, Y); link(cslot['ReturnValue'], setp['self']); link(poff['ReturnValue'], setp['InPosition']); ex(bhc, setp)
shw = g.call('/Script/UMG.Widget:SetVisibility', 'ShowColumn', X0 + 3500, Y, InVisibility='HitTestInvisible'); link(gcol['Output'], shw['self']); ex(setp, shw)
# this column is taken: a second label with the same name gets the next one
used = array_set(g, STR, X0 + 3750, Y, name='ClaimColumn'); link(g.get('PassNames', ARR(STR), X0 + 3600, Y + 200, name='PassNamesClaim')['PassNames'], used['TargetArray'])
link(fnd['ReturnValue'], used['Index']); used.set('Item', '|used|'); ex(shw, used)

# ---- debug log whenever the result changes
Y = 8000
dbg2 = g.get('Dbg', STR, 4800, Y + 250, name='DbgCmp'); ldbg = g.get('LastDbg', STR, 4800, Y + 350, name='LastDbgCmp')
same_d = g.call(KSTR + ':EqualEqual_StrStr', 'SameDbg', 5000, Y + 250); link(dbg2['Dbg'], same_d['A']); link(ldbg['LastDbg'], same_d['B'])
bdd = g.branch(5000, Y, 'BrDbgChanged'); link(same_d['ReturnValue'], bdd['Condition']); ex(tl, bdd, 'Completed')
sld = g.setv('LastDbg', STR, 5250, Y + 100, name='RememberDbg'); link(dbg2['Dbg'], sld['LastDbg']); ex(bdd, sld, 'else')
bgl = g.get('Building', ACTOR, 5250, Y + 450, name='BuildingLog')
bln = g.call(KSL + ':GetDisplayName', 'BuildingLogName', 5450, Y + 450); link(bgl['Building'], bln['Object'])
lgd = log(g, 5900, Y + 100, msg_pin=concat(g, 5500, Y + 300, 'TraitPeek: ', bln['ReturnValue'], ' ', dbg2['Dbg']), name='LogNames'); ex(sld, lgd)
open(OUT + '/WBP_TraitPeek.txt', 'w').write(g.text())


# =========================================================================== MAPLOAD (Actor)
# Variables: Debug (Boolean), Peek (User Widget object reference)
LAYER = M + 'WBP_TraitLayer'
LAYER_CLS = bp_cls_ref(LAYER)
MAPLOAD_CLS = "/Script/Engine.BlueprintGeneratedClass'%s.%s_C'" % (MAPLOAD, MAPLOAD.split('/')[-1])
UW = OBJ('/Script/UMG.UserWidget')
g = Graph(MAPLOAD)

def api_call(g, fn, x, y, name=None, **kw):
    a = modapi(g, x - 250, y + 150)
    n = g.call(API + ':' + fn, name or fn, x, y, **kw)
    link(a['ReturnValue'], n['self'])
    return n

bp = g.event('/Script/Engine.Actor', 'ReceiveBeginPlay', [], 'Begin', 0, 0)
evL = g.custom_event('OnLoaded', [], 0, 400)
bl = g.add(BG + 'K2Node_AddDelegate', 'BindLoaded',
           ['DelegateReference=(MemberParent="%s",MemberName="onLoadingFinished")' % cls_ref(API)], 400, 0)
bl.pin('execute', EXEC); bl.pin('then', EXEC, out=True)
bl.pin('self', OBJ(API), friendly='NSLOCTEXT("K2Node", "Target", "Target")')
d = bl.pin('Delegate', T('delegate'))
d.memref = 'MemberParent="/Script/CoreUObject.Package\'/Script/SystemCore\'",MemberName="ModAPI_OnEvent__DelegateSignature"'
link(modapi(g, 200, 200)['ReturnValue'], bl['self'])
evL['OutputDelegate'].memref = 'MemberParent="%s",MemberName="OnLoaded"' % MAPLOAD_CLS
link(evL['OutputDelegate'], d); ex(bp, bl)

# OnLoaded: Debug from debug.txt, layer + worker widgets, input
rdf = api_call(g, 'ReadModTextFile', 300, 400, name='ReadDebugFile', modName='TraitPeek', Filename='debug.txt'); ex(evL, rdf)
dfe = g.call(KSTR + ':IsEmpty', 'DebugFileEmpty', 550, 550); link(rdf['ReturnValue'], dfe['InString'])
dfn = g.call(KML + ':Not_PreBool', 'DebugFileThere', 750, 550); link(dfe['ReturnValue'], dfn['A'])
sdbg = g.setv('Debug', BOOL, 650, 400, name='SetDebug'); link(dfn['ReturnValue'], sdbg['Debug']); ex(rdf, sdbg)
pc = g.call('/Script/Engine.GameplayStatics:GetPlayerController', 'PC', 900, 650)
cl_ = g.create_widget(LAYER, 1000, 400, name='CreateLayer'); link(pc['ReturnValue'], cl_['OwningPlayer']); ex(sdbg, cl_)
avl = g.call('/Script/UMG.UserWidget:AddToViewport', 'LayerToViewport', 1300, 400, ZOrder='5'); link(cl_['ReturnValue'], avl['self']); ex(cl_, avl)
lroot = g.add(BG + 'K2Node_VariableGet', 'LayerRootOfLayer', ['VariableReference=(MemberParent="%s",MemberName="Root")' % LAYER_CLS], 1300, 600)
lroot.pin('Root', CANVAS, out=True); lroot.pin('self', T('object', obj=LAYER_CLS), friendly='NSLOCTEXT("K2Node", "Target", "Target")')
link(cl_['ReturnValue'], lroot['self'])
cp = g.create_widget(PEEK, 1550, 400, name='CreatePeek'); link(pc['ReturnValue'], cp['OwningPlayer']); ex(avl, cp)
sp = g.setv('Peek', UW, 1850, 400, name='SetPeek'); link(cp['ReturnValue'], sp['Peek']); ex(cp, sp)
# hand over the layer canvas and the Debug flag by property name (no typed cross-Blueprint pins)
spr = g.call(KSL + ':SetObjectPropertyByName', 'GiveLayer', 2100, 400, PropertyName='LayerRoot')
link(cp['ReturnValue'], spr['Object']); link(lroot['Root'], spr['Value']); ex(sp, spr)
spd = g.call(KSL + ':SetBoolPropertyByName', 'GiveDebug', 2400, 400, PropertyName='Debug')
link(cp['ReturnValue'], spd['Object']); link(sdbg['Output_Get'], spd['Value']); ex(spr, spd)
ei = g.call('/Script/Engine.Actor:EnableInput', 'EnableKeys', 2700, 400); link(pc['ReturnValue'], ei['PlayerController']); ex(spd, ei)
slf = g.add(BG + 'K2Node_Self', 'Me', [], 2550, 600); slf.pin('self', T('object', sub='self'), out=True); link(slf['self'], ei['self'])
lr = log(g, 3100, 400, msg='TraitPeek ready (1.0)', name='LogReady'); ex(ei, lr)

# any key / mouse button released in the world (works while paused, not consumed) -> kick
kA = g.add(BG + 'K2Node_InputKey', 'AnyKey', ['InputKey=AnyKey', 'bConsumeInput=False', 'bExecuteWhenPaused=True'], 0, 1200)
kA.pin('Pressed', EXEC, out=True); kA.pin('Released', EXEC, out=True); kA.pin('Key', STRUCT('/Script/InputCore.Key'), out=True)
pg = g.get('Peek', UW, 150, 1400, name='PeekGet')
pv = g.call(KSL + ':IsValid', 'PeekReady', 350, 1450); link(pg['Peek'], pv['Object'])
bpv = g.branch(350, 1200, 'BrPeekReady'); link(pv['ReturnValue'], bpv['Condition']); ex(kA, bpv, 'Released')
inv = g.call('/Script/UMG.Widget:IsInViewport', 'PeekRunning', 600, 1400); link(pg['Peek'], inv['self'])
brn = g.branch(650, 1200, 'BrPeekRunning'); link(inv['ReturnValue'], brn['Condition']); ex(bpv, brn)
rst = g.call(KSL + ':SetDoublePropertyByName', 'RestartPeek', 950, 1100, PropertyName='Waited', Value='0.0'); link(pg['Peek'], rst['Object']); ex(brn, rst)
rsb = g.call(KSL + ':SetBoolPropertyByName', 'RebindPeek', 1250, 1100, PropertyName='Bound', Value='false'); link(pg['Peek'], rsb['Object']); ex(rst, rsb)
stv = g.call('/Script/UMG.UserWidget:AddToViewport', 'StartPeek', 950, 1300, ZOrder='6'); link(pg['Peek'], stv['self']); ex(brn, stv, 'else')
open(OUT + '/BP_MapLoad.txt', 'w').write(g.text())


# =========================================================================== validation
import re as _re
def validate(path):
    txt = open(path, encoding='utf-8').read()
    names = set(_re.findall(r'Begin Object Class=\S+ Name="([^"]+)"', txt))
    bad = []
    for m in _re.finditer(r'LinkedTo=\(([^)]*)\)', txt):
        for ref in m.group(1).split(','):
            ref = ref.strip()
            if ref and ref.split(' ')[0] not in names: bad.append(ref)
    return len(names), bad

for gname in ('WBP_TraitChip', 'WBP_TraitColumn', 'WBP_TraitPeek', 'BP_MapLoad'):
    n, bad = validate(os.path.join(OUT, gname + '.txt'))
    print(gname, n, 'nodes', 'BAD LINKS' if bad else 'links ok', bad[:5])
