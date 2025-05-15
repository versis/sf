import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";

export const metadata = {
  title: "Shadenfreude - Color Card Generator",
  description: "Create your own Pantone-like color cards with Shadenfreude.",
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
      <body className={cn(GeistSans.className, "antialiased dark")}>
        <Toaster position="top-center" richColors />
        {children}
      </body>
    </html>
  );
}
