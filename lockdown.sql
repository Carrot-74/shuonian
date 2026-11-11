-- 朔念锁表：public 下所有表只允许小猫本人账号读写，anon 一律拒绝
-- 萧朔的 MCP 用 secret key（service_role），不受 RLS 限制
do $$
declare
  owner_uid constant uuid := '3aad6cd1-ab1a-4985-bed4-fefdbefedf0e';
  r record;
  t text;
begin
  -- 1. 删掉所有旧规则（包括各种"谁都能读写"的规则）
  for r in select tablename, policyname from pg_policies where schemaname = 'public' loop
    execute format('drop policy %I on public.%I', r.policyname, r.tablename);
  end loop;

  -- 2. 每张表开 RLS，只认小猫这一个 uid；收回 anon 的所有权限
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t);
    execute format(
      'create policy owner_only on public.%I for all to authenticated using (auth.uid() = %L::uuid) with check (auth.uid() = %L::uuid)',
      t, owner_uid, owner_uid
    );
    execute format('revoke all on public.%I from anon', t);
  end loop;
end $$;
