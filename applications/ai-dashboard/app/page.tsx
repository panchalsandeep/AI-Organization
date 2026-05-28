import Link from "next/link";

export default function Home() {
  return (
    <main className="page-container">
      <section className="hero">
        <h1>AI Operations System</h1>
        <p>Centralized AI operating system frontend for agent queries and workflows.</p>
      </section>

      <section className="card">
        <h2>Dashboard</h2>
        <p>Access the centralized AI Operations dashboard to run queries and execute workflows.</p>
        <Link href="/dashboard">
          <button>Open Dashboard</button>
        </Link>
      </section>

      <section className="card">
        <h2>Backend API</h2>
        <p>The backend API is available at <code>http://localhost:8000</code> by default.</p>
        <p>Endpoints:</p>
        <ul>
          <li><code>POST /agent/query</code></li>
          <li><code>POST /workflow/execute</code></li>
        </ul>
      </section>
    </main>
  );
}
