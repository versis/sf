import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

interface BatchCardRequest {
  extended_ids: string[];
}

interface CardData {
  id: string;
  v: string | null;
  h: string | null;
  bv: string | null;
  bh: string | null;
}

export async function POST(request: NextRequest) {
  try {
    const body: BatchCardRequest = await request.json();
    const { extended_ids } = body;

    if (!extended_ids || !Array.isArray(extended_ids) || extended_ids.length === 0) {
      return NextResponse.json({ error: 'extended_ids array is required' }, { status: 400 });
    }

    // Call the Python API batch endpoint
    const apiResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/batch-retrieve-cards`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ extended_ids }),
    });

    if (!apiResponse.ok) {
      console.error('Python API batch request failed:', apiResponse.status);
      return NextResponse.json({ error: 'Failed to fetch cards from API' }, { status: apiResponse.status });
    }

    const batchResult = await apiResponse.json();
    
    // Transform the response to match the frontend format
    const transformedCards: Record<string, CardData | null> = {};
    
    for (const [extendedId, cardData] of Object.entries(batchResult.cards)) {
      if (cardData && typeof cardData === 'object') {
        const card = cardData as any;
        transformedCards[extendedId] = {
          id: extendedId,
          v: card.front_vertical_image_url || null,
          h: card.front_horizontal_image_url || null,
          bv: card.back_vertical_image_url || null,
          bh: card.back_horizontal_image_url || null,
        };
      } else {
        transformedCards[extendedId] = null;
      }
    }

    return NextResponse.json({ cards: transformedCards });

  } catch (error) {
    console.error('Error in batch card retrieval:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
} 