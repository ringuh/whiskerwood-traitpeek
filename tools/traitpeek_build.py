"""Generates the Blueprint paste text (T3D) for TraitPeek's graphs into tools/out/.
Usage: python tools/traitpeek_build.py   (needs the modkit's jmap, see t3d.py)
Paste each file into the matching asset's graph (Ctrl+A, Delete, Ctrl+V), compile.
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

def log(g, x, y, msg_pin=None, msg=None):
    a = modapi(g, x, y + 160)
    n = g.call(API + ':LogMessage', 'Log', x + 250, y, doPrependDate='true')
    link(a['ReturnValue'], n['self'])
    if msg_pin: link(msg_pin, n['Msg'])
    elif msg: n.set('Msg', msg)
    return n

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

def is_valid(g, pin, x, y):
    n = g.call(KSL + ':IsValid', 'Valid', x, y); link(pin, n['Object']); return n['ReturnValue']

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
bare = g.call(KSTR + ':Replace', 'StripPrefix', 2250, 300, From='trait.', To='', SearchCase='IgnoreCase'); link(rn['ReturnValue'], bare['SourceString'])
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
g = Graph(PEEK)
WIDGET = OBJ('/Script/UMG.Widget'); ACTOR = OBJ('/Script/Engine.Actor'); AG = OBJ(AGENT)
COLT = T('object', obj=bp_cls_ref(COLUMN))
VIEW = OBJ('/Script/ProjectArco.ArcoView')
NAVI = '/Script/SystemCore.NaviUi'

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

# ---- Construct
con = g.event('/Script/UMG.UserWidget', 'Construct', [], 'Construct', 0, -1000)
lg0 = log(g, 300, -1000, msg='TraitPeek ready (portrait mode)'); ex(con, lg0)

# ---- Tick throttle + find open building view
tk = g.event('/Script/UMG.UserWidget', 'Tick', [('MyGeometry', GEO), ('InDeltaTime', FLT)], 'Tick', 0, 0)
ag = g.get('Acc', DBL, 0, 250)
add = g.call(KML + ':Add_DoubleDouble', 'AccAdd', 200, 250); link(ag['Acc'], add['A']); link(tk['InDeltaTime'], add['B'])
sa = g.setv('Acc', DBL, 450, 0); link(add['ReturnValue'], sa['Acc']); ex(tk, sa)
ge = g.call(KML + ':GreaterEqual_DoubleDouble', 'Due', 650, 250, B='0.2'); link(sa['Output_Get'], ge['A'])
bdue = g.branch(700, 0, 'BrDue'); link(ge['ReturnValue'], bdue['Condition']); ex(sa, bdue)
sa0 = g.setv('Acc', DBL, 950, 0, value='0.0', name='ResetAcc'); ex(bdue, sa0)
san = g.setv('Anchor', WIDGET, 1200, 0, name='ClearAnchor'); ex(sa0, san)
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
bok = g.branch(2400, 0, 'BrViewOK'); link(okc['ReturnValue'], bok['Condition']); ex(pl, bok, 'LoopBody')
sanc = g.setv('Anchor', WIDGET, 2700, 0, name='SetAnchor'); link(pl['Array Element'], sanc['Anchor']); ex(bok, sanc)
sbld = g.setv('Building', ACTOR, 2950, 0, name='SetBuilding'); link(cx['Context'], sbld['Building']); ex(sanc, sbld)

# ---- no building open: remove columns
Y = 1000
ang = g.get('Anchor', WIDGET, 2100, Y + 250, name='AnchorGet')
bany = g.branch(2400, Y, 'BrFound'); link(is_valid(g, ang['Anchor'], 2250, Y + 250), bany['Condition']); ex(pl, bany, 'Completed')
rl0, rl0end = remove_columns(g, 2700, Y + 600, 'A'); ex(bany, rl0, 'else', 'Exec')
slk = g.setv('LastKey', STR, 4000, Y + 800, value='', name='ForgetKey'); ex(rl0end, slk)

# ---- building open: collect workers + key
wg = g.get('Workers', ARR(AG), 2700, Y + 250, name='WorkersClr')
clw = g.arr('Array_Clear', AG, 2800, Y, name='ClearWorkers'); link(wg['Workers'], clw['TargetArray']); ex(bany, clw)
bg = g.get('Building', ACTOR, 3000, Y + 250, name='BuildingKey')
dn = g.call(KSL + ':GetDisplayName', 'BuildingName', 3200, Y + 250); link(bg['Building'], dn['Object'])
sk = g.setv('Key', STR, 3100, Y, name='StartKey'); link(dn['ReturnValue'], sk['Key']); ex(clw, sk)
gaa = g.call('/Script/Engine.GameplayStatics:GetAllActorsOfClass', 'AllWhiskers', 3400, Y, ActorClass=AGENT)
gaa['OutActors'].t = ARR(AG); ex(sk, gaa)
al = g.macro('ForEachLoop', AG, 3700, Y, name='WhiskerLoop'); link(gaa['OutActors'], al['Array']); ex(gaa, al, 'then', 'Exec')
wp = g.call('/Script/ProjectArco.Prototype_Agent:GetWorkplace', 'Workplace', 3900, Y + 300); link(al['Array Element'], wp['self'])
bg2 = g.get('Building', ACTOR, 3900, Y + 420, name='BuildingCmp')
eq = g.call(KML + ':EqualEqual_ObjectObject', 'WorksHere', 4150, Y + 300); link(wp['ReturnValue'], eq['A']); link(bg2['Building'], eq['B'])
bwh = g.branch(4100, Y, 'BrWorksHere'); link(eq['ReturnValue'], bwh['Condition']); ex(al, bwh, 'LoopBody')
wg2 = g.get('Workers', ARR(AG), 4300, Y + 200, name='WorkersAdd')
aw = g.arr('Array_Add', AG, 4400, Y, name='AddWorker'); link(wg2['Workers'], aw['TargetArray']); link(al['Array Element'], aw['NewItem']); ex(bwh, aw)
kg = g.get('Key', STR, 4600, Y + 250, name='KeyGet')
wdn = g.call(KSL + ':GetDisplayName', 'WhiskerName', 4600, Y + 350); link(al['Array Element'], wdn['Object'])
kc = concat(g, 4800, Y + 250, kg['Key'], wdn['ReturnValue'])
sk2 = g.setv('Key', STR, 4700, Y, name='GrowKey'); link(kc, sk2['Key']); ex(aw, sk2)

# ---- rebuild columns if key changed
Y = 2400
kg2 = g.get('Key', STR, 3700, Y + 250, name='KeyCmp'); lkg = g.get('LastKey', STR, 3700, Y + 350, name='LastKeyCmp')
same = g.call(KSTR + ':EqualEqual_StrStr', 'SameKey', 3900, Y + 250); link(kg2['Key'], same['A']); link(lkg['LastKey'], same['B'])
bsame = g.branch(3900, Y, 'BrSame'); link(same['ReturnValue'], bsame['Condition']); ex(al, bsame, 'Completed')
slk2 = g.setv('LastKey', STR, 4150, Y + 150, name='RememberKey'); link(kg2['Key'], slk2['LastKey']); ex(bsame, slk2, 'else')
rl1, rl1end = remove_columns(g, 4400, Y + 150, 'B'); ex(slk2, rl1, 'then', 'Exec')
wg3 = g.get('Workers', ARR(AG), 5400, Y + 400, name='WorkersLoop')
cl = g.macro('ForEachLoop', AG, 5600, Y + 150, name='ColumnLoop'); link(wg3['Workers'], cl['Array']); ex(rl1end, cl, 'then', 'Exec')
ccw = g.create_widget(COLUMN, 5900, Y + 150, name='CreateColumn'); ex(cl, ccw, 'LoopBody')
csd = g.bpcall(COLUMN, 'SetData', [('InAgent', AG), ('InTable', NAME)], name='ColumnSetData', x=6200, y=Y + 150)
link(ccw['ReturnValue'], csd['self']); link(cl['Array Element'], csd['InAgent']); ex(ccw, csd)
rootg = g.get('Root', OBJ('/Script/UMG.CanvasPanel'), 6300, Y + 450, name='RootGet')
addc = g.call('/Script/UMG.CanvasPanel:AddChildToCanvas', 'AddToRoot', 6500, Y + 150); link(rootg['Root'], addc['self']); link(ccw['ReturnValue'], addc['Content']); ex(csd, addc)
sas = g.call('/Script/UMG.CanvasPanelSlot:SetAutoSize', 'ColAutoSize', 6800, Y + 150, InbAutoSize='true'); link(addc['ReturnValue'], sas['self']); ex(addc, sas)
sal = g.call('/Script/UMG.CanvasPanelSlot:SetAlignment', 'ColAlign', 7050, Y + 150, InAlignment='(X=0.500000,Y=0.000000)'); link(addc['ReturnValue'], sal['self']); ex(sas, sal)
hid = g.call('/Script/UMG.Widget:SetVisibility', 'ColHidden', 7300, Y + 150, InVisibility='Collapsed'); link(ccw['ReturnValue'], hid['self']); ex(sal, hid)
cg = g.get('Columns', ARR(COLT), 7400, Y + 450, name='ColumnsAdd')
acol = g.arr('Array_Add', COLT, 7550, Y + 150, name='AddColumn'); link(cg['Columns'], acol['TargetArray']); link(ccw['ReturnValue'], acol['NewItem']); ex(hid, acol)
chs = g.get('m_characteristics', STRUCT('/Script/ProjectArco.AgentCharacteristics'), 7400, Y + 600, owner=AGENT, name='WorkerChars')
link(cl['Array Element'], chs['self'])
props = J()['/Script/ProjectArco.AgentCharacteristics']['properties']
br = g.add(BG + 'K2Node_BreakStruct', 'BreakWorker', ['StructType="/Script/CoreUObject.ScriptStruct\'/Script/ProjectArco.AgentCharacteristics\'"', 'bMadeAfterOverridePinRemoval=True'], 7650, Y + 600)
for i, p in enumerate(props):
    br.header.append('ShowPinForProperties(%d)=(PropertyName="%s",bShowPin=%s,bCanToggleVisibility=True)' % (i, p['name'], p['name'] == 'agentName'))
br.pin('AgentCharacteristics', STRUCT('/Script/ProjectArco.AgentCharacteristics')); br.pin('agentName', STR, out=True)
link(chs['m_characteristics'], br['AgentCharacteristics'])
ng = g.get('ColNames', ARR(STR), 7700, Y + 450, name='ColNamesAdd')
aname = g.arr('Array_Add', STR, 7850, Y + 150, name='AddColName'); link(ng['ColNames'], aname['TargetArray']); link(br['agentName'], aname['NewItem']); ex(acol, aname)

# ---- position columns under matching portraits (every refresh)
Y = 3600
sdb = g.setv('Dbg', STR, 4200, Y, value='names:', name='ResetDbg')
ex(bsame, sdb); ex(cl, sdb, 'Completed')
ang2 = g.get('Anchor', WIDGET, 4300, Y + 300, name='AnchorSearch')
tbc = class_array(g, '/Script/UMG.TextBlock', 4300, Y + 450, name='TextBlockClass')
fd = g.call(NAVI + ':FindDecendentsOfClasses', 'FindTexts', 4500, Y, ignoreHidden='true')
link(ang2['Anchor'], fd['searchRoot']); link(tbc['Array'], fd['candidateClasses'])
# hide while the whisker picker is open
WAP = '/Script/ProjectArco.WorkerAssignmentPanel'
ang3 = g.get('Anchor', WIDGET, 3900, Y - 700, name='AnchorPanel')
wpc = class_array(g, WAP, 3900, Y - 550, name='PanelClass')
fpn = g.call(NAVI + ':FindDecendentsOfClasses', 'FindPanel', 4100, Y - 800, ignoreHidden='false')
link(ang3['Anchor'], fpn['searchRoot']); link(wpc['Array'], fpn['candidateClasses']); ex(sdb, fpn)
p0 = array_get(g, WIDGET, 4400, Y - 600, name='FirstPanel'); link(fpn['ReturnValue'], p0['Array'])
cwp = g.cast(WAP, False, 4400, Y - 800, name='AsPanel'); cwp['AsWorker Assignment Panel'].name = 'AsWorkerAssignmentPanel'
link(p0['Output'], cwp['Object']); ex(fpn, cwp)
sel = g.get('m_isAgentSelectOpen', BOOL, 4650, Y - 600, owner=WAP, name='PickerOpen'); link(cwp['AsWorkerAssignmentPanel'], sel['self'])
bpk = g.branch(4700, Y - 800, 'BrPickerOpen'); link(sel['m_isAgentSelectOpen'], bpk['Condition']); ex(cwp, bpk)
cgh = g.get('Columns', ARR(COLT), 4900, Y - 600, name='ColumnsHide')
hl = g.macro('ForEachLoop', COLT, 5000, Y - 800, name='HideLoop'); link(cgh['Columns'], hl['Array']); ex(bpk, hl, 'then', 'Exec')
hc = g.call('/Script/UMG.Widget:SetVisibility', 'HideColumn', 5300, Y - 800, InVisibility='Collapsed'); link(hl['Array Element'], hc['self']); ex(hl, hc, 'LoopBody')
ex(bpk, fd, 'else'); ex(cwp, fd, 'CastFailed')
tl = g.macro('ForEachLoop', WIDGET, 4850, Y, name='TextLoop'); link(fd['ReturnValue'], tl['Array']); ex(fd, tl, 'then', 'Exec')
wn = g.call(KSL + ':GetDisplayName', 'TextWidgetName', 5000, Y + 300); link(tl['Array Element'], wn['Object'])
isn = g.call(KSTR + ':EqualEqual_StrStr', 'IsNameLabel', 5200, Y + 300, B='string_name'); link(wn['ReturnValue'], isn['A'])
bnl = g.branch(5150, Y, 'BrNameLabel'); link(isn['ReturnValue'], bnl['Condition']); ex(tl, bnl, 'LoopBody')
ctb = g.cast('/Script/UMG.TextBlock', False, 5300, Y + 150, name='AsTextBlock'); link(tl['Array Element'], ctb['Object'])
ctb['AsText Block'].name = 'AsTextBlock'
gtx = g.call('/Script/UMG.TextBlock:GetText', 'LabelText', 5550, Y + 450); link(ctb['AsTextBlock'], gtx['self'])
t2s = g.call(KTXT + ':Conv_TextToString', 'LabelString', 5800, Y + 450); link(gtx['ReturnValue'], t2s['InText'])
dbg = g.get('Dbg', STR, 5800, Y + 250, name='DbgGrow')
sdb2 = g.setv('Dbg', STR, 5450, Y, name='AddDbgName'); idxs = g.call(KSTR + ':Conv_IntToString', 'IdxStr', 6400, Y + 150)
link(concat(g, 6000, Y + 250, dbg['Dbg'], ' ', t2s['ReturnValue'], '=', idxs['ReturnValue']), sdb2['Dbg']); ex(bnl, ctb); ex(ctb, sdb2)
ng2 = g.get('ColNames', ARR(STR), 6000, Y + 600, name='ColNamesFind')
fnd = array_find(g, STR, 6200, Y + 500, name='FindColumn'); link(ng2['ColNames'], fnd['TargetArray']); link(t2s['ReturnValue'], fnd['ItemToFind'])
link(fnd['ReturnValue'], idxs['inInt'])
ge0 = g.call(KML + ':GreaterEqual_IntInt', 'HasColumn', 6450, Y + 500, B='0'); link(fnd['ReturnValue'], ge0['A'])
bhc = g.branch(5750, Y, 'BrHasColumn'); link(ge0['ReturnValue'], bhc['Condition']); ex(sdb2, bhc)
# portrait = first UserWidget parent of the label

pgeo = g.call('/Script/UMG.Widget:GetCachedGeometry', 'PortraitGeo', 6300, Y + 250); link(tl['Array Element'], pgeo['self'])
psz = g.call('/Script/UMG.SlateBlueprintLibrary:GetLocalSize', 'PortraitSize', 6550, Y + 350); link(pgeo['ReturnValue'], psz['Geometry'])
pbk = g.call(KML + ':BreakVector2D', 'PortraitWH', 6750, Y + 350); link(psz['ReturnValue'], pbk['InVec'])
half = g.call(KML + ':Multiply_DoubleDouble', 'HalfWidth', 6950, Y + 300, B='0.5'); link(pbk['X'], half['A'])
bot = g.call(KML + ':MakeVector2D', 'BottomCenter', 7150, Y + 350); link(half['ReturnValue'], bot['X']); link(pbk['Y'], bot['Y'])
pabs = g.call('/Script/UMG.SlateBlueprintLibrary:LocalToAbsolute', 'PortraitAbs', 7350, Y + 300); link(pgeo['ReturnValue'], pabs['Geometry']); link(bot['ReturnValue'], pabs['LocalCoordinate'])
ploc = g.call('/Script/UMG.SlateBlueprintLibrary:AbsoluteToLocal', 'PortraitLocal', 7600, Y + 300); link(tk['MyGeometry'], ploc['Geometry']); link(pabs['ReturnValue'], ploc['AbsoluteCoordinate'])
poff = g.call(KML + ':Add_Vector2DVector2D', 'NudgeDown', 7850, Y + 300, B='(X=0.000000,Y=88.000000)'); link(ploc['ReturnValue'], poff['A'])
cg3 = g.get('Columns', ARR(COLT), 6300, Y + 700, name='ColumnsGet')
gcol = array_get(g, COLT, 6550, Y + 700, name='ColumnForName'); link(cg3['Columns'], gcol['Array']); link(fnd['ReturnValue'], gcol['Dimension 1'])
cslot = g.call('/Script/UMG.WidgetLayoutLibrary:SlotAsCanvasSlot', 'ColumnSlot', 6800, Y + 700); link(gcol['Output'], cslot['Widget'])
setp = g.call('/Script/UMG.CanvasPanelSlot:SetPosition', 'PlaceColumn', 8100, Y); link(cslot['ReturnValue'], setp['self']); link(poff['ReturnValue'], setp['InPosition']); ex(bhc, setp)
shw = g.call('/Script/UMG.Widget:SetVisibility', 'ShowColumn', 8350, Y, InVisibility='HitTestInvisible'); link(gcol['Output'], shw['self']); ex(setp, shw)
dbg3 = g.get('Dbg', STR, 8350, Y + 300, name='DbgPos')
ptn = g.call(KSL + ':GetDisplayName', 'PortraitName', 8350, Y + 400); link(tl['Array Element'], ptn['Object'])
pps = g.call(KSTR + ':Conv_Vector2dToString', 'PosStr', 8350, Y + 500); link(poff['ReturnValue'], pps['InVec'])
ncol = g.arr('Array_Length', COLT, 8350, Y + 600, name='ColCount', pure=True); cg4 = g.get('Columns', ARR(COLT), 8200, Y + 650, name='ColumnsCount'); link(cg4['Columns'], ncol['TargetArray'])
ncs = g.call(KSTR + ':Conv_IntToString', 'ColCountStr', 8500, Y + 600); link(ncol['ReturnValue'], ncs['inInt'])
sdb3 = g.setv('Dbg', STR, 8600, Y, name='AddDbgPos'); link(concat(g, 8600, Y + 300, dbg3['Dbg'], ' @', ptn['ReturnValue'], ' ', pps['ReturnValue'], ' cols=', ncs['ReturnValue']), sdb3['Dbg']); ex(shw, sdb3)
# debug log when the list of labels changes
Y = 4800
dbg2 = g.get('Dbg', STR, 4800, Y + 250, name='DbgCmp'); ldbg = g.get('LastDbg', STR, 4800, Y + 350, name='LastDbgCmp')
same_d = g.call(KSTR + ':EqualEqual_StrStr', 'SameDbg', 5000, Y + 250); link(dbg2['Dbg'], same_d['A']); link(ldbg['LastDbg'], same_d['B'])
bdd = g.branch(5000, Y, 'BrDbgChanged'); link(same_d['ReturnValue'], bdd['Condition']); ex(tl, bdd, 'Completed')
sld = g.setv('LastDbg', STR, 5250, Y + 100, name='RememberDbg'); link(dbg2['Dbg'], sld['LastDbg']); ex(bdd, sld, 'else')
bgl = g.get('Building', ACTOR, 5250, Y + 450, name='BuildingLog')
bln = g.call(KSL + ':GetDisplayName', 'BuildingLogName', 5450, Y + 450); link(bgl['Building'], bln['Object'])
lgd = log(g, 5700, Y + 100, msg_pin=concat(g, 5500, Y + 300, 'TraitPeek: ', bln['ReturnValue'], ' ', dbg2['Dbg'])); ex(sld, lgd)
open(OUT + '/WBP_TraitPeek.txt', 'w').write(g.text())


# =========================================================================== MAPLOAD
g = Graph(MAPLOAD)
bp = g.event('/Script/Engine.Actor', 'ReceiveBeginPlay', [], 'Begin', 0, 0)
pc = g.call('/Script/Engine.GameplayStatics:GetPlayerController', 'PC', 100, 250)
cw = g.create_widget(PEEK, 350, 0, name='CreatePeek'); link(pc['ReturnValue'], cw['OwningPlayer']); ex(bp, cw)
av = g.call('/Script/UMG.UserWidget:AddToViewport', 'ToViewport', 700, 0, ZOrder='5'); link(cw['ReturnValue'], av['self']); ex(cw, av)
lg = log(g, 1000, 0, msg='TraitPeek: overlay created'); ex(av, lg)
open(OUT + '/BP_MapLoad.txt', 'w').write(g.text())
print('done', [f for f in os.listdir(OUT)])
