-- 朔念 RLS 备份（锁表前，2026-11-11 导出）
-- 用途：锁表出问题时，在 Supabase SQL Editor 里整段执行，恢复到锁表前的状态
-- 注意：恢复后数据又会变成谁都能读写，只用于应急

-- 1. 每张表的 RLS 开关
alter table public.conflicts enable row level security;
alter table public.diary enable row level security;
alter table public.drives enable row level security;
alter table public.emotion_predictions disable row level security;
alter table public.emotions enable row level security;
alter table public.handoff enable row level security;
alter table public.health_data disable row level security;
alter table public.imprints enable row level security;
alter table public.milestones disable row level security;
alter table public.mood_letters disable row level security;
alter table public.personality_arcs enable row level security;
alter table public.promises enable row level security;
alter table public.shuonian_self enable row level security;
alter table public.undercurrents enable row level security;
alter table public.user_profile disable row level security;

-- 2. 删掉锁表时新加的规则
drop policy if exists owner_only on public.conflicts;
drop policy if exists owner_only on public.diary;
drop policy if exists owner_only on public.drives;
drop policy if exists owner_only on public.emotion_predictions;
drop policy if exists owner_only on public.emotions;
drop policy if exists owner_only on public.handoff;
drop policy if exists owner_only on public.health_data;
drop policy if exists owner_only on public.imprints;
drop policy if exists owner_only on public.milestones;
drop policy if exists owner_only on public.mood_letters;
drop policy if exists owner_only on public.personality_arcs;
drop policy if exists owner_only on public.promises;
drop policy if exists owner_only on public.shuonian_self;
drop policy if exists owner_only on public.undercurrents;
drop policy if exists owner_only on public.user_profile;

-- 3. 原来的规则
create policy "Allow all" on public.diary as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.drives as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.emotions as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.handoff as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.imprints as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.personality_arcs as PERMISSIVE for ALL to public using (true) with check (true);
create policy "Allow all" on public.undercurrents as PERMISSIVE for ALL to public using (true) with check (true);
create policy "anon all" on public.shuonian_self as PERMISSIVE for ALL to anon using (true) with check (true);
create policy anon_all_conflicts on public.conflicts as PERMISSIVE for ALL to public using (true) with check (true);
create policy anon_all_promises on public.promises as PERMISSIVE for ALL to public using (true) with check (true);

-- 4. 原来 anon 的权限
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.diary to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.milestones to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.personality_arcs to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.emotion_predictions to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.health_data to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.mood_letters to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.promises to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.undercurrents to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.handoff to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.user_profile to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.imprints to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.shuonian_self to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.drives to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.emotions to anon;
grant INSERT, SELECT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER on public.conflicts to anon;
