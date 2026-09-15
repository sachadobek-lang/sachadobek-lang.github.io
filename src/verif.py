"""Contrôle de syntaxe du script avant publication : chaînes fermées, blocs équilibrés."""
import io, sys
src = io.open('index.html', encoding='utf-8').read()
js = src[src.index('<script>')+8 : src.rindex('</script>')]
i, n, ligne = 0, len(js), 1
pile, erreurs = [], []
precedent, crochet = '', False
paires = {')': '(', ']': '[', '}': '{'}
while i < n:
    c = js[i]
    if c == '\n': ligne += 1; i += 1; continue
    if not c.isspace(): pass
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
