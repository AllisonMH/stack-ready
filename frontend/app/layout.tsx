import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "StackReady",
  description: "Full-stack interview prep powered by RAG",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="min-h-full flex flex-col bg-zinc-950 text-zinc-100 antialiased">
        <header className="border-b border-brand-primary/40 px-6 py-4 flex items-center justify-between bg-brand-primary/10">
          <Link href="/" className="font-semibold text-lg tracking-tight text-brand-accent">
            StackReady <span className="text-brand-soft/60 font-normal text-sm">/ interview prep</span>
          </Link>
          <nav className="flex gap-6 text-sm text-brand-soft/70">
            <Link href="/" className="hover:text-brand-accent transition-colors">Ask</Link>
            <Link href="/traces" className="hover:text-brand-accent transition-colors">Traces</Link>
          </nav>
        </header>
        <main className="flex-1 flex flex-col">{children}</main>
      </body>
    </html>
  );
}
