"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_SUBTITLE, APP_TITLE } from "@/lib/theme";

const LINKS = [
  { href: "/home", label: "Home" },
  { href: "/discovery", label: "Discovery" },
  { href: "/culture", label: "Culture" },
  { href: "/curate", label: "Curate" },
  { href: "/role-fit", label: "Role Fit" },
];

export function SiteNav() {
  const pathname = usePathname();

  return (
    <nav className="site-nav">
      <Link href="/role-fit" className="brand">
        {APP_TITLE}
      </Link>
      <span style={{ color: "var(--muted)", fontSize: "0.75rem", width: "100%", marginBottom: "0.25rem" }}>
        {APP_SUBTITLE}
      </span>
      {LINKS.map(({ href, label }) => (
        <Link
          key={href}
          href={href}
          className={pathname === href || (href === "/role-fit" && pathname === "/") ? "active" : ""}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
