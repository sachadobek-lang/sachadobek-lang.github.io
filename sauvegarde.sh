#!/bin/bash
# Enregistre les changements du projet et les envoie sur GitHub quand c'est possible.
# Silencieux quand rien n'a bougé.
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")" || exit 1

python3 src/build.py >/dev/null 2>&1

[ -z "$(git status --porcelain)" ] && exit 0

git add -A
git -c commit.gpgsign=false commit -q -m "Sauvegarde automatique du $(date '+%-d %B %Y à %H:%M')"

if git remote get-url origin >/dev/null 2>&1; then
  git push -q origin main 2>/dev/null && echo "$(date '+%F %T') envoyé sur GitHub" >> sauvegarde.log \
    || echo "$(date '+%F %T') enregistré en local, GitHub injoignable" >> sauvegarde.log
else
  echo "$(date '+%F %T') enregistré en local (pas encore de dépôt GitHub)" >> sauvegarde.log
fi
