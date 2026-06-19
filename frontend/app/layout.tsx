/**
 * Root layout for GuardianEye dashboard application.
 * Applies a dark-first visual baseline suitable for defense monitoring workflows.
 */
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "GuardianEye: Ukraine Air Raid Defense Analytics",
  description:
    "Defense analytics dashboard for air raid alert intelligence, forecasting, and interception monitoring.",
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps): JSX.Element {
  try {
    return (
      <html lang="en" className="dark">
        <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
          <main className="mx-auto w-full max-w-7xl px-6 py-8">{children}</main>
        </body>
      </html>
    );
  } catch (error) {
    console.error("Root layout rendering failed", error);
    return (
      <html lang="en" className="dark">
        <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
          <main className="mx-auto w-full max-w-7xl px-6 py-8">Unable to render GuardianEye layout.</main>
        </body>
      </html>
    );
  }
}
