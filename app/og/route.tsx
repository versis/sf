/* eslint-disable @next/next/no-img-element */

import { ImageResponse } from "next/server";

export const runtime = "edge";
export const preferredRegion = ["iad1"];

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  const title = searchParams.get("title") || "shadefreude";
  const description = searchParams.get("description") || "Create beautiful color reference cards";

  const geistSemibold = await fetch(
    new URL("../../assets/geist-semibold.ttf", import.meta.url)
  ).then((res) => res.arrayBuffer());

  // Create a sample color palette for the preview
  const colors = [
    "#FF5252", // Red
    "#FF9800", // Orange
    "#FFEB3B", // Yellow
    "#4CAF50", // Green
    "#2196F3", // Blue
    "#9C27B0", // Purple
  ];

  return new ImageResponse(
    (
      <div
        tw="flex h-full w-full bg-white"
        style={{ fontFamily: "Geist Sans" }}
      >
        <div tw="flex flex-col absolute h-full w-full p-16">
          {/* Header */}
          <div tw="flex items-center mb-8">
            <div 
              tw="text-6xl font-bold tracking-tight" 
              style={{ color: "#000000" }}
            >
              {title}
            </div>
          </div>
          
          {/* Color Showcase */}
          <div tw="flex flex-row w-full my-6 gap-4">
            {colors.map((color, i) => (
              <div key={i} tw="flex flex-col">
                <div 
                  tw="h-24 w-24 rounded-lg shadow-lg" 
                  style={{ backgroundColor: color }}
                />
              </div>
            ))}
          </div>
          
          {/* Description */}
          <div 
            tw="text-3xl mt-6" 
            style={{ color: "#555555" }}
          >
            {description}
          </div>
          
          {/* Sample Card Preview */}
          <div tw="absolute bottom-16 right-16 flex items-center">
            <div 
              tw="flex flex-col rounded-lg shadow-xl overflow-hidden border border-gray-200"
              style={{ width: "320px", height: "450px" }}
            >
              <div 
                style={{ backgroundColor: "#2196F3", height: "225px" }}
              />
              <div tw="bg-white p-6 flex flex-col" style={{ height: "225px" }}>
                <div tw="text-2xl font-bold text-black mb-1">ALPINE BLUE</div>
                <div tw="text-gray-500 mb-2">[&apos;ælpaɪn bluː]</div>
                <div tw="text-sm text-gray-700">A deep blue reminiscent of clear mountain skies and alpine lakes.</div>
                <div tw="mt-auto text-lg font-bold text-black">sf.tinker.institute</div>
              </div>
            </div>
          </div>
          
          <div tw="absolute bottom-16 left-16 text-xl font-semibold text-gray-700">
            part of tinker.institute
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      fonts: [
        {
          name: "geist",
          data: geistSemibold,
          style: "normal",
        },
      ],
    }
  );
}
