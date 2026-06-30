import Header from './components/Header';
import Dashboard from './components/Dashboard';
import Footer from './components/Footer';
import DocsPage from './pages/DocsPage';
import StatusPage from './pages/StatusPage';
import TermsPage from './pages/TermsPage';

export default function App() {
  const page = {
    '/docs': <DocsPage />,
    '/status': <StatusPage />,
    '/terms': <TermsPage />,
  }[window.location.pathname] ?? <Dashboard />;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--color-canvas)' }}>
      <Header />
      <main className="flex-1">{page}</main>
      <Footer />
    </div>
  );
}
