import { ImageResponse } from "next/server";

export const runtime = "edge";
export const contentType = "image/png";
export const size = { width: 1200, height: 630 };

// Twitter will use the OpenGraph image if we define the size here
// In Next.js 13.5 and later, we can just use the `export { default } from "./opengraph-image"`
// but we'll create a complete file for compatibility
export default async function Image({ params }: { params: {} }) {
  // Reuse the same component from opengraph-image.tsx
  const OGImage = (await import("./opengraph-image")).default;
  return OGImage({ params });
} 