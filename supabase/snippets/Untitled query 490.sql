select
    proname,
    proargnames
from pg_proc
where proname = 'match_operational_memory';