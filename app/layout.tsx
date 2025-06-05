import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Metadata } from 'next';
import Footer from '@/components/Footer';

const siteUrl = process.env.NEXT_PUBLIC_API_URL; // Removed fallback

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl!), // Keep non-null assertion for URL constructor
  title: "shadefreude: The Digital Postcard Service | tinker.institute",
  description: "Your everyday photo, having its moment — / Polaroid vibes. / AI brains. / No cringe. Hopefully. — Pick a color from your photo and watch AI transform it into a digital postcard with a custom color name and unique story.",
  alternates: {
    canonical: `${siteUrl}/`
  },
  openGraph: {
    title: "shadefreude: The Digital Postcard Service",
    description: "Your everyday photo, having its moment — / Polaroid vibes. / AI brains. / No cringe. Hopefully. — Pick a color from your photo and watch AI transform it into a digital postcard with a custom color name and unique story.",
    type: "website",
    url: `${siteUrl}/`,
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "shadefreude - The Digital Postcard Service",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "shadefreude: The Digital Postcard Service",
    description: "Your everyday photo, having its moment — / Polaroid vibes. / AI brains. / No cringe. Hopefully. — Pick a color from your photo and watch AI transform it into a digital postcard with a custom color name and unique story.",
    images: ["/og.png"],
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
