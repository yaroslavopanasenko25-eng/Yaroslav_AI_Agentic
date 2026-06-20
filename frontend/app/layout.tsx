/**
 * Root layout for GuardianEye dashboard application.
 * Applies a dark-first visual baseline suitable for defense monitoring workflows.
 */
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { SettingsProvider } from "../components/SettingsProvider";
import Navigation from "../components/Navigation";
import AIAgentIcon from "../components/AIAgentIcon";
import "./globals.css"; // Ensure globals are imported if there are any

export const metadata: Metadata = {
  title: "GuardianEye: Ukraine Air Raid Defense Analytics",
  description:
    "Defense analytics dashboard for air raid alert intelligence, forecasting, and interception monitoring.",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 antialiased transition-colors duration-300">
        <SettingsProvider>
          <Navigation />
          <main className="mx-auto w-full max-w-[1400px] px-4 py-6 md:px-8">
            {children}
          </main>
          <AIAgentIcon />
        </SettingsProvider>
      </body>
    </html>
  );
}
