-- SentinelFlow schema (PostgreSQL 16). Idempotent: safe to apply on every start-up.
-- Aggregates keep their nested parts (entities, decisions, principal) as jsonb so a
-- row maps 1:1 to a frozen domain object; columns exist for everything we query by.

create table if not exists incidents (
  id          text not null,
  tenant_id   text not null,
  team        text not null,
  status      text not null,
  severity    smallint not null,
  verdict     text,
  alert_ids   jsonb not null,
  entities    jsonb not null,
  created_at  timestamptz not null,
  seq         bigserial,
  primary key (tenant_id, id)
);

create table if not exists alerts (
  id           text not null,
  tenant_id    text not null,
  incident_id  text not null,
  fingerprint  text not null,
  source       text not null,
  rule_id      text not null,
  title        text not null,
  observed_at  timestamptz not null,
  entities     jsonb not null,
  raw          jsonb not null,   -- untrusted text, never interpreted
  primary key (tenant_id, id)
);
create index if not exists alerts_fingerprint on alerts (tenant_id, fingerprint, observed_at desc);

create table if not exists approvals (
  id              text not null,
  tenant_id       text not null,
  run_id          text not null,
  action          jsonb not null,
  required_role   text not null,
  required_count  smallint not null,
  expires_at      timestamptz not null,
  decisions       jsonb not null,
  status          text not null,
  seq             bigserial,
  primary key (tenant_id, id)
);
create index if not exists approvals_run on approvals (tenant_id, run_id);
create index if not exists approvals_pending on approvals (tenant_id) where status = 'pending';

create table if not exists workflow_runs (
  id           text not null,
  tenant_id    text not null,
  workflow     text not null,
  incident_id  text not null,
  alert_id     text not null,
  initiator    jsonb not null,
  status       text not null,
  updated_at   timestamptz not null,
  primary key (tenant_id, id)
);

create table if not exists audit_events (
  tenant_id  text not null,
  seq        bigint not null,
  at         timestamptz not null,
  actor      text not null,
  verb       text not null,
  resource   text not null,
  outcome    text not null,
  details    jsonb not null,
  prev_hash  char(64) not null,
  hash       char(64) not null,
  primary key (tenant_id, seq)
);

-- Post-incident report tickets (the "ticketing system" until a real one is plugged in).
create sequence if not exists ticket_seq;
create table if not exists tickets (
  tenant_id    text not null,
  incident_id  text not null,
  id           text not null,
  title        text not null,
  body         text not null,
  primary key (tenant_id, incident_id)
);

-- Row-level security (defence in depth). Every repository transaction first runs
-- set_config('app.tenant_id', <tenant>, true); rows of other tenants are then invisible
-- and cannot be written, even by a query that forgets its tenant filter. FORCE applies
-- the policy to the table owner too; superusers still bypass RLS, so the application
-- must connect as an ordinary role.
do $$
declare
  t text;
begin
  foreach t in array array['incidents', 'alerts', 'approvals', 'workflow_runs', 'audit_events', 'tickets'] loop
    execute format('alter table %I enable row level security', t);
    execute format('alter table %I force row level security', t);
    if not exists (select 1 from pg_policies where tablename = t and policyname = 'tenant_isolation') then
      execute format(
        'create policy tenant_isolation on %I'
        ' using (tenant_id = current_setting(''app.tenant_id'', true))'
        ' with check (tenant_id = current_setting(''app.tenant_id'', true))', t);
    end if;
  end loop;
end $$;
