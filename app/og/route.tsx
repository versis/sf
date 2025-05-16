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

  return new ImageResponse(
    (
      <div
        tw="flex flex-col items-center justify-center h-full w-full bg-white"
        style={{ fontFamily: "Geist Sans" }}
      >
        <div tw="flex items-center justify-center">
          <span tw="text-8xl font-bold">shade</span>
          <span tw="text-8xl font-bold bg-white border-4 border-blue-600 px-4 mx-2" style={{ borderColor: "#0000FF" }}>freude</span>
        </div>
        <div tw="mt-8 text-3xl text-gray-600">
          part of <span tw="text-gray-800">tinker.institute</span>
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
