// Quick test of metadata generation
function formatCardDate(isoString) {
  try {
    const date = new Date(isoString);
    return date.toLocaleString('sv-SE', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit', 
      minute: '2-digit'
    }).replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/, '$1/$2/$3 $4');
  } catch (error) {
    return new Date().toLocaleString('sv-SE').replace(/(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})/, '$1/$2/$3 $4');
  }
}

function generateCardTitle(location, createdAt) {
  let title = 'shadefreude: You have a new postcard';
  
  if (location) {
    title += ` from ${location}!`;
  }
  
  if (createdAt) {
    const formattedDate = formatCardDate(createdAt);
    title += ` Posted: ${formattedDate}`;
  }
  
  return title;
}

function generateCardDescription(extendedId, noteText) {
  if (noteText && noteText.trim()) {
    const truncatedNote = noteText.length > 30 
      ? noteText.substring(0, 27) + "..."
      : noteText;
    return `Card ID "${extendedId}": ${truncatedNote}`;
  }
  
  return "A unique AI-generated color postcard that turns everyday photos into shareable moments with custom color names and insights.";
}

// Test cases
console.log('=== TITLE EXAMPLES ===');
console.log('WITH location:', generateCardTitle('Poland', '2025-05-28T19:55:08.970126+00:00'));
console.log('WITHOUT location:', generateCardTitle(undefined, '2025-05-28T19:55:08.970126+00:00'));

console.log('\n=== DESCRIPTION EXAMPLES ===');
console.log('WITH note:', generateCardDescription('000000545 FE F', 'BeeARD meetup'));
console.log('WITHOUT note:', generateCardDescription('000000545 FE F', undefined));
console.log('LONG note:', generateCardDescription('000000545 FE F', 'This is a very long note that exceeds thirty characters')); 