import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://sf.tinker.institute'),
  title: "shadefreude - unique color cards (part of tinker.institute)",
  description: "Create beautiful color reference cards with Shadefreude",
  icons: [
    { rel: "icon", url: "/sf-icon.png" },
    { rel: "apple-touch-icon", url: "/sf-icon.png" },
  ],
  openGraph: {
    type: "website",
    title: "shadefreude - unique color cards (part of tinker.institute)",
    description: "Create beautiful color reference cards with shadefreude",
    siteName: "shadefreude",
    images: [
      {
        url: "https://sf.tinker.institute/og?title=shadefreude&description=Create beautiful color reference cards",
        width: 1200,
        height: 630,
        alt: "Shadefreude Card Preview"
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "shadefreude - unique color cards (part of tinker.institute)",
    description: "Create beautiful color reference cards with shadefreude",
    images: [
      {
        url: "https://sf.tinker.institute/og?title=Shadefreude&description=Create beautiful color reference cards",
        width: 1200,
        height: 630,
        alt: "Shadefreude Card Preview"
      },
    ],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head></head>
      <body className={cn(GeistSans.className, "antialiased")}>
        <Toaster position="top-center" richColors />
        {children}
      </body>
    </html>
  );
}
