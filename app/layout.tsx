import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://sf.tinker.institute'),
  title: "shadenfreude card (part of tinker.institute)",
  description: "Create your own Pantone-like color cards with shadenfreude.",
  icons: [
    { rel: "icon", url: "/sf-icon.png" },
    { rel: "apple-touch-icon", url: "/sf-icon.png" },
  ],
  openGraph: {
    images: [
      {
        url: "/og?title=Shadenfreude",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    images: [
      {
        url: "/og?title=Shadenfreude",
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
