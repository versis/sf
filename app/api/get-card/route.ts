import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Ensures the route is treated as dynamic

export async function GET(request: NextRequest) {
  try {
    // Use request.nextUrl for robust access to URL parts
    const searchParams = request.nextUrl.searchParams;
    const orientation = searchParams.get('orientation') || 'horizontal';
    const color = searchParams.get('color') || '#000000';
    
    // In a real implementation, you would:
    // 1. Check if the card with these parameters exists in your storage (database, S3, etc.)
    // 2. If it exists, return it directly
    // 3. If not, you would either:
    //    a. Return a 404 or an error
    //    b. Generate the card on-the-fly if you have all needed resources
    
    // For demo purposes, this route redirects to the main page with query parameters.
    // This allows the main page (client component) to attempt to load card details
    // from sessionStorage or make further API calls if needed.

    // Construct the redirect URL safely using request.nextUrl.origin
    const redirectUrl = new URL(request.nextUrl.origin);
    redirectUrl.pathname = '/'; // Assuming the redirect is to the root of the application
    redirectUrl.searchParams.set('orientation', orientation);
    redirectUrl.searchParams.set('color', color);

    return NextResponse.redirect(redirectUrl);
    
    // Alternative: In a real implementation with actual storage and image retrieval:
    // const cardExists = false; // Replace with actual check
    // if (cardExists) {
    //   // const imageBuffer = await fs.readFile(pathToImage);
    //   // return new NextResponse(imageBuffer, {
    //   //   headers: {
    //   //     'Content-Type': 'image/png',
    //   //     'Cache-Control': 'public, max-age=31536000, immutable',
    //   //   },
    //   // });
    // } else {
    //   // return NextResponse.json({ error: 'Card not found' }, { status: 404 });
    // }

  } catch (error) {
    console.error('Error in /api/get-card:', error);
    // Check if the error is a known type or has a digest for specific handling
    const errorMessage = error instanceof Error ? error.message : 'Failed to retrieve card';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
} 