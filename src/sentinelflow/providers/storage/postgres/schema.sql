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
