import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "./providers";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL("http://localhost:3000"),
  title: {
    default: "ProcureAI Intelligence",
    template: "%s · ProcureAI",
  },
  description:
    "AI-powered purchasing decisions, execution and validation for enterprise operations.",
  applicationName: "ProcureAI",
  openGraph: {
    title: "ProcureAI Intelligence",
    description: "Observe. Reason. Decide. Act. Validate. Recover.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geist.variable} ${mono.variable} font-sans`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
