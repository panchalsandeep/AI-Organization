# AI Dashboard

Frontend for the AI Operations System.

## Setup

1. Navigate to the dashboard folder:

```bash
cd applications/ai-dashboard
```

2. Install dependencies:

```bash
npm install
```

3. Run the Next.js development server:

```bash
npm run dev
```

4. Open the app at `http://localhost:3000`.

## Backend

Start the backend from the repository root:

```bash
.venv/bin/python -m uvicorn backend.api.main:app --reload
```

The frontend expects the backend to be available at `http://localhost:8000`.

## Notes

- The frontend calls the backend `agent/query` and `workflow/execute` endpoints.
- If your backend uses a different URL, set `NEXT_PUBLIC_API_URL` in `.env.local` or the environment.

## Vercel deployment

This app can be deployed on Vercel directly from the `applications/ai-dashboard` folder.

1. Create a new Vercel project and point it to `applications/ai-dashboard`.
2. Use the existing `package.json` and `next.config.mjs`.
3. Set `NEXT_PUBLIC_API_URL` in Vercel Environment Variables to your backend URL (for example `https://api.yourdomain.com`).
4. Deploy.

After deployment, your frontend will be hosted at a Vercel URL such as `https://<project-name>.vercel.app`.
