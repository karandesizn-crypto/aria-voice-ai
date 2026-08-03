import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Fraunces, Manrope } from "next/font/google";
import { SiteHeader } from "@/components/site-header";
import "@livekit/components-styles";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
});

const sans = Manrope({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Aria — Voice AI Platform",
  description: "Realtime multimodal voice agents with memory, tools, and presence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${display.variable} ${sans.variable}`}>
        <ClerkProvider>
          <div className="app-shell">
            <SiteHeader />
            <main className="app-main">{children}</main>
          </div>
        </ClerkProvider>
      </body>
    </html>
  );
}
