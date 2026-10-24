import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '../context/AuthContext';
import Navbar from '../components/common/Navbar';

export const metadata: Metadata = {
  title: 'Gayatri Cloud — Adaptive Education Platform',
  description:
    'Course-independent adaptive AI tutoring platform for learners, teachers, and institutions.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased text-slate-900">
        <AuthProvider>
          <Navbar />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
