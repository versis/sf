/* eslint-disable @next/next/no-img-element */
import { ImageResponse } from "next/server";
import { NextRequest } from "next/server";

export const runtime = "edge";
export const contentType = "image/png";
export const size = { width: 1200, height: 630 };

export default async function Image({ params }: { params: { رنگ?: string, نام_رنگ?: string } }, request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const color = searchParams.get("color") || "#2196F3";
  const colorName = searchParams.get("colorName") || "COLOR REFERENCE CARD";

  const geistSemibold = await fetch(
    new URL("../../assets/geist-semibold.ttf", import.meta.url)
  ).then((res) => res.arrayBuffer());

  return new ImageResponse(
    (
      <div
        tw="flex h-full w-full bg-white"
        style={{ fontFamily: "Geist Sans" }}
      >
        <div tw="flex flex-col absolute h-full w-full p-16">
          {/* Header */}
          <div tw="flex items-center mb-6">
            <div 
              tw="text-6xl font-bold tracking-tight" 
              style={{ color: "#000000" }}
            >
              shadefreude
            </div>
          </div>
          
          {/* Description */}
          <div 
            tw="text-3xl mt-6" 
            style={{ color: "#555555" }}
          >
            View this personalized color reference card created with shadefreude.
          </div>
          
          {/* Sample Card Preview - Now Dynamic */}
          <div tw="absolute flex items-center justify-center w-full h-full">
            <div 
              tw="flex flex-col rounded-lg shadow-xl overflow-hidden border border-gray-200"
              style={{ width: "350px", height: "500px" }}
            >
              <div 
                style={{ backgroundColor: color, height: "250px" }}
              />
              <div tw="bg-white p-6 flex flex-col" style={{ height: "250px" }}>
                <div tw="text-2xl font-bold text-black mb-1 truncate" style={{ maxWidth: '300px' }}>{colorName.toUpperCase()}</div>
                <div tw="text-gray-500 mb-2">{color}</div>
                <div tw="text-sm text-gray-700">
                  A unique color reference card. Perfect for designers, artists, and color enthusiasts.
                </div>
                <div tw="mt-auto text-lg font-bold text-black">sf.tinker.institute</div>
              </div>
            </div>
          </div>
          
          <div tw="absolute bottom-16 left-16 text-xl font-semibold">
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