import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic'; // Ensures the route is treated as dynamic

export async function GET(request: NextRequest) {
  try {
    // Use request.nextUrl for robust access to URL parts
    const searchParams = request.nextUrl.searchParams;
    const orientation = searchParams.get('orientation') || 'horizontal';
    const color = searchParams.get('color') || '#000000';
    
    // Construct the redirect URL safely using request.nextUrl.origin
    const redirectUrl = new URL(request.nextUrl.origin);
    redirectUrl.pathname = '/'; // Assuming the redirect is to the root of the application
    redirectUrl.searchParams.set('orientation', orientation);
    redirectUrl.searchParams.set('color', color);

    return NextResponse.redirect(redirectUrl);

  } catch (error) {
    console.error('Error in /api/get-card:', error);
    // Check if the error is a known type or has a digest for specific handling
    const errorMessage = error instanceof Error ? error.message : 'Failed to retrieve card';
    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
} 