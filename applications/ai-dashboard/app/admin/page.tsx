import Link from "next/link";

export default function AdminHome() {
  return (
    <main className="page-container">
      <section className="hero">
        <h1>Admin Console</h1>
        <p>Manage tenants, permissions, audit logs, and compliance settings for your AI Operations System.</p>
      </section>

      <section className="card">
        <h2>Administration</h2>
        <ul>
          <li>
            <Link href="/admin/tenants">Tenant Management</Link>
          </li>
          <li>
            <Link href="/admin/rbac">RBAC Management</Link>
          </li>
          <li>
            <Link href="/admin/audit">Audit Trail</Link>
          </li>
          <li>
            <Link href="/admin/compliance">Compliance Dashboard</Link>
          </li>
        </ul>
      </section>
    </main>
  );
}
