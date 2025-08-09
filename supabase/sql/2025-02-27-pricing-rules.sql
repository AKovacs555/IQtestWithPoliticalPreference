-- Pricing rules table
create table if not exists public.pricing_rules (
  id uuid primary key default gen_random_uuid(),
  country char(2) not null,
  product text not null check (product in ('retry','pro_month')),
  price_jpy int not null,
  active boolean not null default true,
  updated_at timestamptz default now()
);

create index if not exists pricing_rules_country_product_idx
  on public.pricing_rules(country, product);
