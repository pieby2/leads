import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth/next';
import Link from 'next/link';
// Note: We need to import the handler config to get the correct session.
// Wait, we exported handler in route.ts, but not an authOptions object.
// Let's create an authOptions in a lib file or export it from route.ts.

// For now, let's just make a simple layout that has a nav.
export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="dashboard-layout">
      <nav className="dashboard-nav" style={{ padding: '1rem', background: '#1a1a24', display: 'flex', gap: '1rem' }}>
        <Link href="/" style={{ fontWeight: 'bold' }}>VidCompare</Link>
        <Link href="/dashboard">Dashboard</Link>
        <Link href="/billing">Billing</Link>
      </nav>
      <main style={{ padding: '2rem' }}>
        {children}
      </main>
    </div>
  );
}
