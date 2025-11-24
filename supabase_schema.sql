-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Robots Table
create table public.robots (
  id text primary key,
  name text not null,
  status text default 'offline',
  last_seen timestamptz default now(),
  created_at timestamptz default now()
);

-- 2. Jobs Table
create table public.jobs (
  id uuid primary key default uuid_generate_v4(),
  robot_id text references public.robots(id),
  workflow text not null,
  status text default 'pending', -- pending, running, success, failed
  logs text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 3. Enable Realtime for these tables
alter publication supabase_realtime add table public.robots;
alter publication supabase_realtime add table public.jobs;

-- 4. Row Level Security (RLS) - Optional for now, open for development
alter table public.robots enable row level security;
alter table public.jobs enable row level security;

create policy "Allow all access" on public.robots for all using (true);
create policy "Allow all access" on public.jobs for all using (true);
