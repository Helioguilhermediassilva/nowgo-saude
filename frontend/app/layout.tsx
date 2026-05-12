import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { DegradationBanner } from "@/components/dashboard/degradation-banner";
import { Header } from "@/components/dashboard/header";
import { Sidebar } from "@/components/dashboard/sidebar";
import { getPipelineHealth } from "@/lib/dashboard-server";
import { cn } from "@/lib/utils";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "NowGo Saúde — Painel Operacional",
  description: "Plataforma operacional AI-native para a saúde pública do Distrito Federal.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Pipeline health drives the global degradation banner so every operational
  // view inherits the same data-quality signal as the home dashboard.
  const health = await getPipelineHealth();
  return (
    <html lang="pt-BR" className={cn(geistSans.variable, geistMono.variable)}>
      <body className="font-sans antialiased">
        <div className="flex min-h-screen bg-background text-foreground">
          <Sidebar />
          <div className="flex min-w-0 flex-1 flex-col">
            <Header />
            <DegradationBanner health={health} />
            {children}
          </div>
        </div>
      </body>
    </html>
  );
}
