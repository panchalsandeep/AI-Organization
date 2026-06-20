import Link from "next/link";
import React from "react";

export const metadata = {
  title: "Admin Console",
  description: "Admin console for AI Operations System",
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="page-container">
      <nav className="admin-nav">
        <Link href="/admin">Home</Link>
        <Link href="/admin/login">Login</Link>
        <Link href="/admin/tenants">Tenants</Link>
        <Link href="/admin/rbac">RBAC</Link>
        <Link href="/admin/audit">Audit</Link>
        <Link href="/admin/compliance">Compliance</Link>
      </nav>
      <div>{children}</div>
    </div>
  );
}
