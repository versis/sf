import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic'; // Ensure fresh data on each request

// Initialize Supabase client
// Ensure your environment variables are correctly set in your Vercel project
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY; // Use service role key for server-side access

if (!supabaseUrl) {
  console.error("Supabase URL is not defined in environment variables (NEXT_PUBLIC_SUPABASE_URL).");
}
if (!supabaseServiceKey) {
  console.error("Supabase Service Role Key is not defined in environment variables (SUPABASE_SERVICE_ROLE_KEY).");
}

// We can initialize client outside the handler if Supabase env vars are present
const supabase = supabaseUrl && supabaseServiceKey ? createClient(supabaseUrl, supabaseServiceKey) : null;

interface CardDataFromDB {
  id: number;
  extended_id: string;
  hex_color: string;
  status: string;
  metadata?: { // Make metadata optional and define its expected structure
    card_name?: string;
    ai_info?: {
      colorName?: string; // AI might use a different key
      phoneticName?: string;
      article?: string;
      description?: string;
    };
    // Add other metadata fields you might want to return
  };
  front_horizontal_image_url?: string;
  front_vertical_image_url?: string;
  note_text?: string;
  has_note?: boolean;
  back_horizontal_image_url?: string;
  back_vertical_image_url?: string;
  created_at: string;
  updated_at: string;
}

// Utility function to extract ID from extended_id
function extractIdFromExtendedId(extendedId: string): number | null {
  if (!extendedId || typeof extendedId !== 'string') {
    return null;
  }
  
  try {
    const parts = extendedId.trim().split(' ');
    if (parts.length < 3) {
      return null;
    }
    
    const paddedId = parts[0];
    if (!/^\d+$/.test(paddedId)) {
      return null;
    }
    
    return parseInt(paddedId, 10);
  } catch {
    return null;
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { extended_id: string } }
) {
  const { extended_id } = params;
  console.log(`[API Route] Attempting to fetch card. Received extended_id: '${extended_id}'`); // Diagnostic log

  if (!supabase) {
    return NextResponse.json({ detail: 'Database client is not initialized. Check server logs.' }, { status: 503 });
  }

  if (!extended_id) {
    return NextResponse.json({ detail: 'extended_id is required' }, { status: 400 });
  }

  try {
    // PERFORMANCE OPTIMIZATION: Try to extract ID and query by primary key first
    const dbId = extractIdFromExtendedId(extended_id);
    
    let data, error;
    
    if (dbId !== null) {
      // Fast path: Query by primary key ID
      console.log(`[API Route] Using optimized ID-based query for db_id: ${dbId}`);
      const response = await supabase
        .from('card_generations')
        .select('id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, created_at, updated_at')
        .eq('id', dbId)
        .single();
      data = response.data;
      error = response.error;
    } else {
      // Fallback: Query by extended_id (slower but backward compatible)
      console.log(`[API Route] Using fallback extended_id query for: ${extended_id}`);
      const response = await supabase
        .from('card_generations')
        .select('id, extended_id, hex_color, status, metadata, front_horizontal_image_url, front_vertical_image_url, note_text, has_note, back_horizontal_image_url, back_vertical_image_url, created_at, updated_at')
        .eq('extended_id', extended_id)
        .single();
      data = response.data;
      error = response.error;
    }

    if (error) {
      console.error('Supabase error:', error);
      if (error.code === 'PGRST116') { // Not found or multiple rows (should not happen with .single() if unique)
        return NextResponse.json({ detail: `Card with extended_id '${extended_id}' not found.` }, { status: 404 });
      }
      return NextResponse.json({ detail: `Database error: ${error.message}` }, { status: 500 });
    }

    if (!data) {
      return NextResponse.json({ detail: `Card with extended_id '${extended_id}' not found.` }, { status: 404 });
    }

    const cardRecord = data as CardDataFromDB;

    // Construct the response. The frontend expects snake_case, which matches the DB.
    // card_name might be in metadata.card_name or metadata.ai_info.colorName
    let cardName = 'Color Card'; // Default
    if (cardRecord.metadata?.card_name) {
        cardName = cardRecord.metadata.card_name;
    } else if (cardRecord.metadata?.ai_info?.colorName) {
        cardName = cardRecord.metadata.ai_info.colorName;
    }

    const responsePayload = {
      id: cardRecord.id,
      extended_id: cardRecord.extended_id,
      hex_color: cardRecord.hex_color,
      card_name: cardName, // This is what the CardData interface on frontend expects
      status: cardRecord.status,
      front_horizontal_image_url: cardRecord.front_horizontal_image_url,
      front_vertical_image_url: cardRecord.front_vertical_image_url,
      note_text: cardRecord.note_text,
      has_note: cardRecord.has_note,
      back_horizontal_image_url: cardRecord.back_horizontal_image_url,
      back_vertical_image_url: cardRecord.back_vertical_image_url,
      ai_name: cardRecord.metadata?.ai_info?.colorName, 
      ai_phonetic: cardRecord.metadata?.ai_info?.phoneticName,
      ai_article: cardRecord.metadata?.ai_info?.article,
      ai_description: cardRecord.metadata?.ai_info?.description,
      created_at: cardRecord.created_at,
      updated_at: cardRecord.updated_at,
    };

    return NextResponse.json(responsePayload);

  } catch (e: any) {
    console.error('Error in GET /api/retrieve-card-by-extended-id:', e);
    return NextResponse.json({ detail: `An unexpected error occurred: ${e.message}` }, { status: 500 });
  }
} 