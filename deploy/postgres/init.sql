-- Runs once when the Postgres volume is created. The application connects as this
-- ordinary role (never a superuser), so row-level security applies to it.
create role sentinel login password 'sentinel';
create database sentinelflow owner sentinel;
