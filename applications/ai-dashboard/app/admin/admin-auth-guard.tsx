"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { getStoredToken } from "./admin-api";

type AdminAuthGuardProps = {
  children: ReactNode;
};

export default function AdminAuthGuard({ children }: AdminAuthGuardProps) {
  const router = useRouter();

  useEffect(() => {
    const token = getStoredToken();
    if (!token) {
      router.replace("/admin/login");
    }
  }, [router]);

  return <>{children}</>;
}
