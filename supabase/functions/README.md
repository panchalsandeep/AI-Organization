Supabase Edge Functions for AI Operations

Functions:
- `agent-query` — accepts `{ query }` and returns an agent response. Currently a placeholder.
- `workflow-execute` — accepts `{ workflow_name, payload }` and returns a placeholder result.

To deploy these functions to your Supabase project (requires the Supabase CLI and being logged in):

1. Install and login to the Supabase CLI: https://supabase.com/docs/guides/cli

2. Deploy each function (replace <project-ref> with your Supabase project ref):

```bash
supabase functions deploy agent-query --project-ref <project-ref>
supabase functions deploy workflow-execute --project-ref <project-ref>
```

3. Set necessary secrets in Supabase (e.g., `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) via the Supabase dashboard or CLI.
