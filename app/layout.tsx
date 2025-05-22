import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Metadata } from 'next';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  metadataBase: new URL('https://sf.tinker.institute'),
  title: "shadefreude: Your Everyday Moments, AI's Extraordinary Postcards | part of tinker.institute",
  description: "Upload a photo from your everyday life, pick a color you love, and watch as AI transforms it into a poetic digital postcard. The shade you choose earns its own evocative title and mini-story, while you add a personal note on the back—turning an ordinary snap into a share-worthy memento.",
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
