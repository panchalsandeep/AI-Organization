import { serve } from "https://deno.land/std@0.201.0/http/server.ts";

serve(async (req: Request) => {
  try {
    const body = await req.json().catch(() => ({}));
    const query = body.query || body.prompt || null;

    if (!query) {
      return new Response(JSON.stringify({ error: "Missing 'query' in request body." }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    const OPENAI_API_KEY = Deno.env.get("OPENAI_API_KEY");
    if (!OPENAI_API_KEY) {
      return new Response(JSON.stringify({ error: "OPENAI_API_KEY not configured in function secrets." }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    }

    // Call OpenAI Chat Completions to generate an agent response
    const prompt = `You are a helpful AI agent. Answer concisely. User query: ${query}`;

    const resp = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: "You are a helpful assistant for AI Operations." },
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
    const assistant = data?.choices?.[0]?.message?.content ?? data?.choices?.[0]?.text ?? null;

    const result = {
      ok: true,
      query,
      assistant: assistant,
      raw: data,
    };

    return new Response(JSON.stringify(result), { status: 200, headers: { 'Content-Type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
});
