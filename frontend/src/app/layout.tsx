import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Gayatri Cloud — Adaptive Education Platform',
  description: 'Course-independent adaptive AI tutoring platform for learners, teachers, and institutions.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased">{children}</body>
    </html>
  );
}
