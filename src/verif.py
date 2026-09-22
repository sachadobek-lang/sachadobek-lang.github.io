"""Contrôle de syntaxe du script avant publication : chaînes fermées, blocs équilibrés."""
import io, sys
# Le fichier à contrôler peut être passé en argument : build.py vérifie un
# brouillon avant de le mettre à la place de index.html, jamais après.
cible = sys.argv[1] if len(sys.argv) > 1 else 'index.html'
src = io.open(cible, encoding='utf-8').read()
import re as _re
blocs = _re.findall(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', src, _re.S)
js = "\n;\n".join(blocs)
i, n, ligne = 0, len(js), 1
pile, erreurs = [], []
precedent, crochet = '', False
paires = {')': '(', ']': '[', '}': '{'}
while i < n:
    c = js[i]
    if c == '\n': ligne += 1; i += 1; continue
    # Une espace ne doit pas devenir « le caractère précédent ». Sans cette
    # ligne, « var P = /jusqu'[àa]/ » était refusé : le caractère d'avant le
    # « / » était l'espace, pas le « = », donc on y voyait une division, on
    # lisait le corps de l'expression comme du texte ordinaire, et
    # l'apostrophe de « jusqu' » y ouvrait une chaîne qui ne se refermait
    # jamais. Le saut de ligne était déjà traité ainsi ; l'espace non.
    # Refuser du code juste est plus coûteux qu'un contrôle un peu large :
    # on apprend à ne plus croire le contrôle.
    if c.isspace(): i += 1; continue
    if c == '/' and i+1 < n and js[i+1] == '/':
        while i < n and js[i] != '\n': i += 1
        continue
    if c == '/' and i+1 < n and js[i+1] == '*':
        i += 2
        while i+1 < n and not (js[i] == '*' and js[i+1] == '/'):
            if js[i] == '\n': ligne += 1
            i += 1
        i += 2; continue
    if c == '/' and precedent in '(,=:[!&|?{};+' :
        i += 1
        while i < n:
            if js[i] == '\\': i += 2; continue
            if js[i] == '[': crochet = True
            elif js[i] == ']': crochet = False
            elif js[i] == '/' and not crochet: break
            elif js[i] == '\n': break
            i += 1
        i += 1; precedent = '/'; continue
    if c in '"\'`':
        ouvre, depart = c, ligne
        i += 1
        while i < n:
            if js[i] == '\\': i += 2; continue
            if js[i] == ouvre: break
            if js[i] == '\n':
                if ouvre != '`':
                    erreurs.append(f"ligne {depart} : chaîne {ouvre} non fermée en fin de ligne")
                    break
                ligne += 1
            i += 1
        i += 1; precedent = ouvre; continue
    if c in '([{': pile.append((c, ligne))
    elif c in ')]}':
        if not pile or pile[-1][0] != paires[c]:
            erreurs.append(f"ligne {ligne} : '{c}' inattendu")
        else: pile.pop()
    precedent = c
    i += 1
for ouvrant, l in pile:
    erreurs.append(f"ligne {l} : '{ouvrant}' jamais fermé")
if erreurs:
    print("SYNTAXE INCORRECTE"); [print("  " + e) for e in erreurs[:8]]; sys.exit(1)
print(f"syntaxe correcte · {len(js)} caractères de script")

# ── Le jugement d'un vrai analyseur ──────────────────────────────────
# Les contrôles ci-dessus voient les chaînes ouvertes et les blocs
# déséquilibrés, mais pas les redéclarations : deux « const u » dans le
# même bloc passent ici et tuent le script entier au chargement. Page
# blanche, aucun avertissement, et build.py qui publie sans broncher.
# C'est arrivé le 18 septembre 2026 ; seule la console du navigateur l'a
# dit. node lit le script comme le fera le navigateur et refuse ce que
# nos expressions régulières ne peuvent pas voir.
# Absent de la machine, on continue sans : un contrôle qu'on ne peut pas
# faire ne doit pas empêcher de publier.
import os as _os, subprocess as _sp, tempfile as _tf
_noeud = _sp.run(["node", "--version"], capture_output=True).returncode == 0
if _noeud:
    for _i, _bloc in enumerate(blocs):
        _f = _tf.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        _f.write(_bloc); _f.close()
        _r = _sp.run(["node", "--check", _f.name], capture_output=True, text=True)
        _os.unlink(_f.name)
        if _r.returncode:
            print("SYNTAXE INCORRECTE — refusée par node")
            # macOS résout /var en /private/var : le chemin rendu par node
            # n'est pas celui qu'on a écrit. On efface tout ce qui ressemble
            # à un chemin temporaire plutôt que de comparer des noms.
            import re as _rex
            for _l in _r.stderr.strip().splitlines()[:8]:
                print("  " + _rex.sub(r'\S*/[\w]+\.js', "bloc %d" % (_i + 1), _l))
            sys.exit(1)
    print("relu par node · %d bloc(s)" % len(blocs))
else:
    print("node absent : le contrôle des redéclarations est sauté")

# ── Un nom déclaré deux fois au niveau supérieur ─────────────────────
# Le 22 septembre 2026, deux défauts de cette forme ont été trouvés le
# même jour, chacun dans sa moitié du fichier, à la main et sans se
# douter que l'autre avait le même : « window.__AGENDA__ = {…} » deux
# fois à cent soixante lignes d'écart, et deux « function
# combienDeFiches ». Dans les deux cas le second écrasait le premier et
# emportait ce qu'il contenait — une fonction d'export appelée par
# l'autre bloc, disparue sans un mot.
# Rien ne le signale : le code est parfaitement légal, node l'accepte,
# la page se charge, et l'appelant croit que la fonction existe. C'est
# la seule classe de défaut de la journée qu'aucun contrôle ne voyait.
# On ne regarde que la colonne zéro — une fonction imbriquée peut
# légitimement porter le nom d'une autre — et on refuse, parce qu'une
# fonction perdue en silence ne se rattrape qu'en console.
import re as _rd, collections as _cl
_doubles = []
for _k, _b in enumerate(blocs):
    _fn = _rd.findall(r'(?m)^(?:async\s+)?function\s+([A-Za-zÀ-ÿ_$][\w$]*)\s*\(', _b)
    _wd = _rd.findall(r'(?m)^(window\.[A-Za-z_$][\w$]*)\s*=\s*[\{\[]', _b)
    for _genre, _lst in (("fonction", _fn), ("objet", _wd)):
        for _nom, _n in _cl.Counter(_lst).items():
            if _n > 1:
                _doubles.append("bloc %d : %s « %s » déclarée %d fois — "
                                "la dernière écrase les autres" % (_k + 1, _genre, _nom, _n))
if _doubles:
    print("DÉCLARÉ DEUX FOIS AU MÊME NIVEAU")
    for _d in _doubles[:8]: print("  " + _d)
    sys.exit(1)

# ── Toute fonction appelée doit exister ──────────────────────────────
import re
declarees = set(re.findall(r'(?:async\s+)?function\s+([A-Za-zÀ-ÿ_$][\w$]*)\s*\(', js))
# var a, b, c;  ·  let x;  ·  const y
for bloc in re.findall(r'(?:var|let|const)\s+([^;\n]+)', js):
    for nom in bloc.split(','):
        nom = nom.strip().split('=')[0].strip()
        if re.match(r'^[A-Za-zÀ-ÿ_$][\w$]*$', nom):
            declarees.add(nom)
declarees |= set(re.findall(r'(?:const|let|var)\s+([A-Za-zÀ-ÿ_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>', js))
declarees |= set(re.findall(r'(?:const|let|var)\s+([A-Za-zÀ-ÿ_$][\w$]*)\s*=', js))
connues = {
    'if','for','while','switch','catch','return','typeof','function','await','new','do','else',
    'Math','Number','String','Object','Array','JSON','Date','Intl','Boolean','Set','Map','parseInt',
    'parseFloat','isNaN','setTimeout','clearTimeout','requestAnimationFrame','FormData','Blob','URL',
    'FileReader','TextDecoder','CSS','Promise','Error','encodeURIComponent','decodeURIComponent','alert',
    'console','document','window','localStorage','performance','fetch','constructor','super','this',
    'not','var','let','const','in','of','delete','void','instanceof','yield','case','throw',
    'confirm','prompt','alert','print','open','close','focus','blur','async','get','set','static',
    'setInterval','clearInterval','requestIdleCallback','structuredClone','queueMicrotask','btoa','atob',
    'Intl','WeakMap','Symbol','Proxy','Reflect','BigInt','RegExp','Function','eval','isFinite','decodeURI',
}
# commentaires, chaînes de texte : rien de tout cela n'est un appel de fonction
sansTexte = re.sub(r'/\*.*?\*/', ' ', js, flags=re.S)
sansTexte = re.sub(r'(?m)//[^\n]*', ' ', sansTexte)
sansTexte = re.sub(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', '""', sansTexte)
appels = set(re.findall(r'(?<![.\w$])([A-Za-zÀ-ÿ_$][\w$]*)\s*\(', sansTexte))
manquantes = sorted(a for a in appels - declarees - connues if not a[0].isupper())
if manquantes:
    print("FONCTIONS APPELÉES MAIS ABSENTES")
    for m in manquantes[:10]:
        print("  " + m)
    sys.exit(1)
print("toutes les fonctions appelées existent")
