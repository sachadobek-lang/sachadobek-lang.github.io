-- ════════════════════════════════════════════════════════════════
--  Cadence — l'administration
--
--  Un back-office simple : voir qui utilise l'application, combien de
--  fiches existent, et rien de plus. Volontairement en lecture seule.
--
--  Être administrateur, c'est être inscrit dans cette table. Pas un
--  drapeau posé sur son propre profil : personne ne doit pouvoir se
--  promouvoir en modifiant sa propre ligne.
-- ════════════════════════════════════════════════════════════════

create table if not exists public.administrateurs (
  id      uuid primary key references auth.users(id) on delete cascade,
  ajoute_le timestamptz not null default now()
);

alter table public.administrateurs enable row level security;

-- La table se lit, ne s'écrit jamais depuis l'application : on ajoute
-- un administrateur à la main, dans le tableau de bord.
drop policy if exists "lecture des administrateurs" on public.administrateurs;
create policy "lecture des administrateurs" on public.administrateurs
  for select using (id = (select auth.uid()));

create or replace function public.est_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.administrateurs where id = auth.uid());
$$;

-- ───────── l'administrateur voit tout, en lecture seule ─────────
do $$
declare t text;
begin
  foreach t in array array['profils','clients','factures','sorties','rendez_vous','taches'] loop
    execute format('drop policy if exists "un admin lit tout" on public.%I;', t);
    execute format(
      'create policy "un admin lit tout" on public.%I
         for select using (public.est_admin());', t);
  end loop;
end $$;

-- ───────── ce que le back-office affiche ─────────
-- Des comptes, pas des contenus : le tableau de bord ne doit jamais
-- donner à lire les factures de quelqu'un ligne à ligne.
create or replace view public.vue_admin_comptes
with (security_invoker = true) as
select
  p.id,
  p.nom,
  p.email,
  p.regime,
  p.cree_le,
  (select count(*) from public.clients  c where c.proprietaire = p.id) as nb_clients,
  (select count(*) from public.factures f where f.proprietaire = p.id) as nb_factures,
  (select coalesce(sum(f.montant), 0) from public.factures f
     where f.proprietaire = p.id and f.statut = 'payee')               as encaisse,
  greatest(
    p.maj_le,
    coalesce((select max(f.maj_le) from public.factures f where f.proprietaire = p.id), p.cree_le)
  ) as derniere_activite
from public.profils p;

comment on view public.vue_admin_comptes is
  'Un compte par ligne, avec de quoi voir l''usage. security_invoker : la vue
   s''exécute avec les droits de celui qui la lit, donc les règles de sécurité
   des tables s''appliquent — seul un administrateur voit autre chose que soi.';
