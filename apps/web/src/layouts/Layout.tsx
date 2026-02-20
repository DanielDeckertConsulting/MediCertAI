/** App shell: sidebar + main content. Mobile-first: hamburger nav on small screens, sidebar on md+. */
import { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

const navItems = [
  { to: "/chat", label: "Chat" },
  { to: "/ai-responses", label: "KI-Antworten" },
  { to: "/folders", label: "Ordner" },
  { to: "/assist", label: "Assistenzmodus" },
  { to: "/admin", label: "Admin" },
  { to: "/ping", label: "Ping" },
];

export default function Layout() {
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);

  const linkClass = (to: string) =>
    `block rounded px-3 py-2.5 text-sm min-h-touch min-w-touch flex items-center ${
      location.pathname.startsWith(to)
        ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900"
        : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
    }`;

  const Sidebar = ({ mobile = false }: { mobile?: boolean }) => (
    <aside
      className={
        mobile
          ? `fixed inset-y-0 left-0 z-50 w-64 border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900 md:hidden ${
              navOpen ? "translate-x-0" : "-translate-x-full"
            } transition-transform duration-200 ease-out`
          : "hidden md:flex md:w-56 md:shrink-0 md:flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900"
      }
    >
      <div className="flex items-center justify-between p-4 md:block">
        <h1 className="text-lg font-semibold text-gray-900 dark:text-white">ClinAI</h1>
        {mobile && (
          <button
            type="button"
            onClick={() => setNavOpen(false)}
            className="min-h-touch min-w-touch flex items-center justify-center rounded p-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Menü schließen"
          >
            ✕
          </button>
        )}
      </div>
      <nav className="space-y-1 px-2">
        {navItems.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            onClick={() => mobile && setNavOpen(false)}
            className={linkClass(to)}
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );

  return (
    <div className="flex min-h-screen overflow-x-hidden">
      <Sidebar mobile />
      <Sidebar />
      {/* Mobile overlay when nav open */}
      {navOpen && (
        <div
          role="button"
          tabIndex={0}
          aria-label="Overlay schließen"
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={() => setNavOpen(false)}
          onKeyDown={(e) => e.key === "Escape" && setNavOpen(false)}
        />
      )}
      <div className="flex flex-1 flex-col min-w-0">
        <header className="sticky top-0 z-30 flex min-h-touch items-center border-b border-gray-200 bg-white px-4 dark:border-gray-700 dark:bg-gray-900 md:hidden">
          <button
            type="button"
            onClick={() => setNavOpen(true)}
            className="min-h-touch min-w-touch -ml-2 flex items-center justify-center rounded p-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="Menü öffnen"
          >
            ☰
          </button>
          <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">ClinAI</span>
        </header>
        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
