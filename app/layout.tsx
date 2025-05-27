import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Metadata } from 'next';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  metadataBase: new URL('https://sf.tinker.institute'),
  title: "shadefreude: Your Everyday Photo, Having Its Moment | tinker.institute",
  description: "/ Polaroid vibes. / AI brains. / No cringe. — Pick a colour and watch AI flip your snap into a digital postcard with its own name and one-line insight.",
  alternates: {
    canonical: "https://sf.tinker.institute/"
  },
  openGraph: {
    title: "shadefreude: Your Everyday Photo, Having Its Moment | tinker.institute",
    description: "/ Polaroid vibes. / AI brains. / No cringe. — AI turns any photo into a share-ready postcard with a custom colour name and witty note.",
    type: "website",
    url: "https://sf.tinker.institute/",
    // images: "https://sf.tinker.institute/og-preview.jpg" // Commented out - image doesn't exist
  },
  twitter: {
    card: "summary_large_image",
    title: "shadefreude: Your Everyday Photo, Having Its Moment | tinker.institute",
    description: "/ Polaroid vibes. / AI brains. / No cringe. — Snap, pick a colour, get a postcard with its own story.",
    // images: "https://sf.tinker.institute/og-preview.jpg" // Commented out - image doesn't exist
  },
  icons: [
    { rel: "icon", url: "/sf-icon.png" },
    { rel: "apple-touch-icon", url: "/sf-icon.png" },
  ]
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script
          defer
          src="https://cloud.umami.is/script.js"
          data-website-id="70281e47-1a9e-4509-8769-fd2e266a4cf5"
        />
      </head>
      <body className={cn(GeistSans.className, "antialiased")}>
        <Toaster position="top-center" richColors />
        {children}
        <Footer />
      </body>
    </html>
  );
}
