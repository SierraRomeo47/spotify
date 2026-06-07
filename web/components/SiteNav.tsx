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
    <header className="site-header">
      <div className="site-header-inner">
        <div className="site-brand-block">
          <Link href="/role-fit" className="brand">
            {APP_TITLE}
          </Link>
          <p className="site-tagline">{APP_SUBTITLE}</p>
        </div>
        <nav className="site-nav-links" aria-label="Main navigation">
          {LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={
                pathname === href || (href === "/role-fit" && pathname === "/")
                  ? "active"
                  : undefined
              }
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
