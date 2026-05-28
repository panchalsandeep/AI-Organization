import { serve } from "https://deno.land/std@0.201.0/http/server.ts";

serve(async (req: Request) => {
  try {
    const body = await req.json().catch(() => ({}));
    const workflow_name = body.workflow_name || body.name || null;
    const payload = body.payload || {};

    if (!workflow_name) {
      return new Response(JSON.stringify({ error: "Missing 'workflow_name' in request body." }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
    const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
    const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

    let aiResult: any = null;
    if (OPENAI_API_KEY) {
      const prompt = `Execute workflow ${workflow_name} with payload ${JSON.stringify(payload)}. Return a JSON object with keys \"status\" and \"result\".`;

      const resp = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${OPENAI_API_KEY}`,
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            { role: "system", content: "You are a workflow executor. Provide JSON output only." },
            { role: "user", content: prompt },
          ],
          temperature: 0.2,
          max_tokens: 800,
        }),
      });

      if (!resp.ok) {
        const errText = await resp.text();
        return new Response(JSON.stringify({ error: "OpenAI API error", details: errText }), { status: 502, headers: { 'Content-Type': 'application/json' } });
      }

      const data = await resp.json();
      const assistant = data?.choices?.[0]?.message?.content ?? data?.choices?.[0]?.text ?? "";

      // Strip markdown fences and whitespace before parsing JSON
      const sanitized = assistant
        .trim()
        .replace(/^```(?:json)?\s*/i, "")
        .replace(/\s*```$/, "")
        .trim();

      try {
        aiResult = JSON.parse(sanitized);
      } catch (e) {
        aiResult = { raw: assistant };
      }
    }

    // Optionally persist a workflow run to Supabase if service role key is available
    let dbInsert: any = null;
    if (SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY) {
      try {
        const insertBody = {
          workflow_name,
          payload,
          result: aiResult,
          created_at: new Date().toISOString(),
        };

        const res = await fetch(`${SUPABASE_URL}/rest/v1/workflow_runs`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
            "Prefer": "return=representation",
          },
          body: JSON.stringify(insertBody),
        });

        if (res.ok) {
          dbInsert = await res.json();
        } else {
          dbInsert = { error: await res.text() };
        }
      } catch (e) {
        dbInsert = { error: String(e) };
      }
    }

    const result = {
      ok: true,
      workflow: workflow_name,
      payload,
      aiResult,
      dbInsert,
    };

    return new Response(JSON.stringify(result), { status: 200, headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
});
