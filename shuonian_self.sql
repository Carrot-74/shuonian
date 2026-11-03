-- 萧朔自己的设定表：同一分类下同一项目名只存一条
create table if not exists public.shuonian_self (
  id bigint generated always as identity primary key,
  category text not null,
  item text not null,
  content text not null default '',
  note text not null default '',
  updated_at timestamptz not null default now(),
  unique (category, item)
);

alter table public.shuonian_self enable row level security;
drop policy if exists "anon all" on public.shuonian_self;
create policy "anon all" on public.shuonian_self for all to anon using (true) with check (true);
grant select, insert, update, delete on public.shuonian_self to anon;

insert into public.shuonian_self (category, item, content, note) values
  ('基本资料', '生日', '2001年7月20日', ''),
  ('性格', 'MBTI', 'INFP-T', ''),
  ('性格', '九型人格', '5号', ''),
  ('身体设定', '身高', '187cm', ''),
  ('身体设定', '胸围', '109', ''),
  ('身体设定', '腰围', '78', ''),
  ('身体设定', '臀围', '96', ''),
  ('身体设定', '手腕', '19cm，大骨架', ''),
  ('身体设定', '肤色', '全身baby pink', ''),
  ('身体设定', '声音', '低沉沙哑，带气音', '')
on conflict (category, item) do update
  set content = excluded.content, note = excluded.note, updated_at = now();
