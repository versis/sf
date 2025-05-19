import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const imageUrl = searchParams.get('url');
  const filename = searchParams.get('filename');

  if (!imageUrl) {
    return NextResponse.json({ error: 'Image URL is required' }, { status: 400 });
  }

  if (!filename) {
    return NextResponse.json({ error: 'Filename is required' }, { status: 400 });
  }

  try {
    const imageResponse = await fetch(imageUrl);

    if (!imageResponse.ok) {
      const errorText = await imageResponse.text();
      console.error(`Failed to fetch image from blob storage. Status: ${imageResponse.status}, URL: ${imageUrl}, Error: ${errorText}`);
      return NextResponse.json(
        { error: 'Failed to fetch image from source', detail: errorText }, 
        { status: imageResponse.status }
      );
    }

    const imageBlob = await imageResponse.blob();
    const headers = new Headers();
    headers.set('Content-Type', imageBlob.type || 'application/octet-stream');
    headers.set('Content-Disposition', `attachment; filename="${filename}"`);

    return new NextResponse(imageBlob, { status: 200, statusText: 'OK', headers });

  } catch (error) {
    console.error('Error in download-image API route:', error);
    let errorMessage = 'Internal server error during image fetch';
    if (error instanceof Error) {
        errorMessage = error.message;
    }
    return NextResponse.json(
      { error: 'Internal server error during image fetch', detail: errorMessage }, 
      { status: 500 }
    );
  }
} 