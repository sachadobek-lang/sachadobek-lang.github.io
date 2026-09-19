-- ════════════════════════════════════════════════════════════════
--  Cura — le coffre
--
--  Pourquoi une seule ligne de JSON plutôt que les six tables du
--  socle, qui sont pourtant écrites juste à côté.
--
--  L'application calcule tout chez elle : aucun total n'est stocké,
--  tout se recalcule à partir des factures. Elle n'a donc rien à
--  demander à une base de données — ni filtre, ni jointure, ni
--  somme. Ce qu'il lui manque n'est pas un moteur de requêtes,
--  c'est un endroit où déposer son état pour ne pas le perdre avec
--  l'appareil, et le retrouver sur un autre.
--
--  Découper cet état en six tables obligerait à tenir deux modèles
--  en parallèle — celui du navigateur et celui du serveur — et à
--  les garder d'accord à chaque évolution. Deux représentations des
--  mêmes chiffres qui peuvent diverger : c'est exactement l'erreur
--  qui a coûté le plus cher sur ce projet.
--
--  Le socle relationnel garde tout son sens le jour où quelqu'un
--  d'autre que le propriétaire devra lire ces données — un
--  comptable, un tableau de bord, une application tierce. Ce jour
--  n'est pas arrivé. Quand il arrivera, ce fichier devra dire
--  pourquoi on a changé, dans le même commit.
-- ════════════════════════════════════════════════════════════════

create table if not exists public.coffres (
  proprietaire uuid primary key references auth.users(id) on delete cascade,

  -- L'état complet de l'application, tel que le navigateur le garde.
  contenu      jsonb not null default '{}'::jsonb,

  -- D'où vient la dernière écriture. Sert à dire « modifié depuis
  -- un autre appareil » plutôt que d'écraser en silence.
  appareil     text not null default '',

  -- Combien de fiches, pour détecter une copie anormalement vide
  -- avant de remplacer une copie pleine.
  fiches       integer not null default 0,

  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

comment on table public.coffres is
  'L''état de l''application, déposé tel quel. Une ligne par compte.';

-- ───────── personne ne voit le coffre d'un autre ─────────
-- Même en s'adressant directement à la base avec la clé publique,
-- qui est dans le code de la page et que tout le monde peut lire.
alter table public.coffres enable row level security;

drop policy if exists "chacun lit son coffre"    on public.coffres;
drop policy if exists "chacun crée son coffre"   on public.coffres;
drop policy if exists "chacun écrit son coffre"  on public.coffres;
drop policy if exists "chacun vide son coffre"   on public.coffres;

create policy "chacun lit son coffre" on public.coffres
  for select using (auth.uid() = proprietaire);

create policy "chacun crée son coffre" on public.coffres
  for insert with check (auth.uid() = proprietaire);

create policy "chacun écrit son coffre" on public.coffres
  for update using (auth.uid() = proprietaire)
          with check (auth.uid() = proprietaire);

create policy "chacun vide son coffre" on public.coffres
  for delete using (auth.uid() = proprietaire);

-- ───────── la date de dernière écriture se tient à jour seule ─────────
-- Si l'application l'envoyait elle-même, une horloge de téléphone mal
-- réglée suffirait à faire passer une vieille copie pour la plus
-- récente, et à écraser la bonne.
create or replace function public.coffre_maj_le()
returns trigger language plpgsql as $$
begin
  new.maj_le = now();
  return new;
end $$;

drop trigger if exists coffre_maj_le on public.coffres;
create trigger coffre_maj_le
  before update on public.coffres
  for each row execute function public.coffre_maj_le();
