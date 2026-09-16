-- ════════════════════════════════════════════════════════════════
--  Cadence — le socle de données
--
--  Principe directeur, hérité de l'application : l'argent n'a qu'une
--  seule source, les factures. Rien n'est stocké en double, aucun
--  total n'est figé en base — tout se recalcule à partir des lignes.
--
--  Chaque table appartient à quelqu'un. La colonne `proprietaire`
--  pointe vers le compte, et la sécurité au niveau des lignes fait le
--  reste : personne ne peut lire ou écrire ce qui n'est pas à lui,
--  même en s'adressant directement à la base.
-- ════════════════════════════════════════════════════════════════

create extension if not exists "pgcrypto";

-- ───────── qui est l'utilisateur ─────────
-- Ces informations apparaissent sur ses factures. Une ligne par compte.
create table if not exists public.profils (
  id              uuid primary key references auth.users(id) on delete cascade,
  nom             text not null default '',
  adresse         text not null default '',
  siret           text not null default '',
  email           text not null default '',
  regime          text not null default 'services'
                  check (regime in ('vente','services','liberal','societe')),
  liberatoire     boolean not null default false,
  tva             boolean not null default false,
  objectif        numeric(12,2) not null default 0,   -- ce qu'il vise par mois
  jours_factures  integer not null default 200,       -- jours travaillés dans l'année
  cree_le         timestamptz not null default now(),
  maj_le          timestamptz not null default now()
);

-- ───────── le carnet de clients ─────────
create table if not exists public.clients (
  id           uuid primary key default gen_random_uuid(),
  proprietaire uuid not null references auth.users(id) on delete cascade,
  nom          text not null,
  projet       text not null default '',
  contact      text not null default '',
  statut       text not null default 'actif'
               check (statut in ('prospect','actif','termine')),
  notes        jsonb not null default '[]'::jsonb,
  exemple      boolean not null default false,
  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

-- ───────── les factures : la seule source de l'argent ─────────
-- `client_nom` est conservé en clair à côté de la référence : une
-- facture doit rester lisible même si la fiche client disparaît, et
-- c'est aussi ce que la loi attend d'une pièce comptable.
create table if not exists public.factures (
  id           uuid primary key default gen_random_uuid(),
  proprietaire uuid not null references auth.users(id) on delete cascade,
  client_id    uuid references public.clients(id) on delete set null,
  client_nom   text not null default '',
  reference    text not null default '',
  objet        text not null default '',
  montant      numeric(12,2) not null default 0 check (montant >= 0),
  emise        date not null default current_date,
  echeance     date,
  statut       text not null default 'envoyee'
               check (statut in ('brouillon','envoyee','payee')),
  mode         text not null default '',             -- virement, chèque, espèces
  payee_le     date,
  exemple      boolean not null default false,
  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

-- ───────── ce qui sort ─────────
-- Dépenses et investissements partagent la même forme ; `nature` les
-- distingue plutôt que deux tables jumelles.
create table if not exists public.sorties (
  id           uuid primary key default gen_random_uuid(),
  proprietaire uuid not null references auth.users(id) on delete cascade,
  nature       text not null default 'depense'
               check (nature in ('depense','investissement')),
  libelle      text not null default '',
  montant      numeric(12,2) not null default 0 check (montant >= 0),
  date         date not null default current_date,
  client_id    uuid references public.clients(id) on delete set null,  -- « c'était pour quel chantier ? »
  exemple      boolean not null default false,
  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

-- ───────── l'agenda ─────────
-- `debut` est en minutes depuis minuit, comme dans l'application, pour
-- que la synchronisation n'ait rien à convertir et ne puisse pas
-- décaler une heure en passant d'un fuseau à l'autre.
create table if not exists public.rendez_vous (
  id           uuid primary key default gen_random_uuid(),
  proprietaire uuid not null references auth.users(id) on delete cascade,
  titre        text not null default '',
  date         date not null,
  debut        integer not null default 540 check (debut between 0 and 1439),
  duree        integer not null default 60 check (duree > 0),
  categorie    text not null default 'travail',
  repetition   text not null default 'none'
               check (repetition in ('none','day','week')),
  client_id    uuid references public.clients(id) on delete set null,
  exemple      boolean not null default false,
  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

-- ───────── les choses à faire ─────────
create table if not exists public.taches (
  id           uuid primary key default gen_random_uuid(),
  proprietaire uuid not null references auth.users(id) on delete cascade,
  titre        text not null,
  echeance     date,
  heure        text not null default '',
  duree        integer not null default 60,
  priorite     text not null default 'normale' check (priorite in ('normale','haute')),
  fait         boolean not null default false,
  client_id    uuid references public.clients(id) on delete set null,
  exemple      boolean not null default false,
  cree_le      timestamptz not null default now(),
  maj_le       timestamptz not null default now()
);

-- ───────── recherches courantes ─────────
create index if not exists idx_clients_proprietaire    on public.clients(proprietaire);
create index if not exists idx_factures_proprietaire   on public.factures(proprietaire, emise desc);
create index if not exists idx_factures_client         on public.factures(client_id);
create index if not exists idx_factures_impayees       on public.factures(proprietaire, echeance)
                                                       where statut <> 'payee';
create index if not exists idx_sorties_proprietaire    on public.sorties(proprietaire, date desc);
create index if not exists idx_rdv_proprietaire        on public.rendez_vous(proprietaire, date);
create index if not exists idx_taches_proprietaire     on public.taches(proprietaire, echeance);

-- ───────── la date de dernière modification, tenue par la base ─────────
-- C'est elle qui arbitre les conflits de synchronisation : on ne peut
-- pas se fier à l'horloge d'un téléphone.
create or replace function public.touche_maj_le()
returns trigger language plpgsql as $$
begin
  new.maj_le = now();
  return new;
end $$;

do $$
declare t text;
begin
  foreach t in array array['profils','clients','factures','sorties','rendez_vous','taches'] loop
    execute format(
      'drop trigger if exists trg_maj_le on public.%I;
       create trigger trg_maj_le before update on public.%I
       for each row execute function public.touche_maj_le();', t, t);
  end loop;
end $$;

-- ───────── le profil naît avec le compte ─────────
create or replace function public.profil_a_la_creation()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profils (id, email, nom)
  values (new.id, coalesce(new.email, ''),
          coalesce(new.raw_user_meta_data->>'full_name', ''))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists trg_profil_a_la_creation on auth.users;
create trigger trg_profil_a_la_creation
after insert on auth.users
for each row execute function public.profil_a_la_creation();

-- ════════════════════════════════════════════════════════════════
--  Sécurité au niveau des lignes
--  Sans ces règles, la clé publique de l'application suffirait à lire
--  les factures de tout le monde. Elles ne sont pas une option.
-- ════════════════════════════════════════════════════════════════

alter table public.profils     enable row level security;
alter table public.clients     enable row level security;
alter table public.factures    enable row level security;
alter table public.sorties     enable row level security;
alter table public.rendez_vous enable row level security;
alter table public.taches      enable row level security;

drop policy if exists "chacun son profil" on public.profils;
create policy "chacun son profil" on public.profils
  for all using (id = (select auth.uid())) with check (id = (select auth.uid()));

do $$
declare t text;
begin
  foreach t in array array['clients','factures','sorties','rendez_vous','taches'] loop
    execute format('drop policy if exists "chacun ses lignes" on public.%I;', t);
    execute format(
      'create policy "chacun ses lignes" on public.%I
         for all using (proprietaire = (select auth.uid()))
         with check (proprietaire = (select auth.uid()));', t);
  end loop;
end $$;
