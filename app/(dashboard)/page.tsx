'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import { shareOrCopy } from '@/lib/shareUtils';
import { COPY_SUCCESS_MESSAGE } from '@/lib/constants';
import { useRouter } from 'next/navigation';
import { Save, SkipForward, PenSquare, /*ChevronDown, ChevronUp,*/ UploadCloud, Wand2, Eye, RotateCcw,
  Copy, Check, Share2, Download, AlertTriangle, MoreHorizontal, X, ExternalLink,
  Image as ImageIcon, Trash2, Info, SquareArrowOutUpRight, Undo2, BookOpenText, ImagePlus } from 'lucide-react';
// Dynamic import for EXIFR to avoid SSR issues and reduce bundle warnings

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'results';

const DUMMY_MESSAGES = [
  "My AI assistant is 'tinkering' with its poetic potential...",
  "Now for its exclusive identity: assigning a unique serial number...",
  "It\'ll look like #000000XXX – each one is one-of-a-kind!...",
  "Then, it gets the special 'FE F' stamp...",
  "The 'FE' stands for 'First Edition'!",
  "And the 'F'? That means this creation is entirely 'Free' for you.",
  "The AI is distilling its essence, crafting a unique name and tale...",
  "Consulting the chromatic soul of your image...",
  "Waking the muses of color for your special hue...",
  "It's taking a final look... (it\'s a bit of a perfectionist!)",
  "Polishing your unique color artifact...",
  "Get ready! Your personal shadefreude is about to debut."
];
const CHAR_TYPING_SPEED_MS = 30;
const NEW_LINE_DELAY_TICKS = Math.floor(2300 / CHAR_TYPING_SPEED_MS);

import { HERO_CARD_IDS } from '@/lib/heroCardConfig';

// Use centralized hero card configuration
const HERO_EXAMPLE_CARD_EXTENDED_IDS = HERO_CARD_IDS;
const SWIPE_THRESHOLD = 50;

export default function HomePage() {
  const router = useRouter();
  const [uploadStepPreviewUrl, setUploadStepPreviewUrl] = useState<string | null>(null);
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [generatedVerticalImageUrl, setGeneratedVerticalImageUrl] = useState<string | null>(null);
  const [generatedHorizontalImageUrl, setGeneratedHorizontalImageUrl] = useState<string | null>(null);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorNameInput, setColorNameInput] = useState<string>('');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const cardDisplayControlsRef = useRef<HTMLDivElement>(null);
  const [userHasInteractedWithColor, setUserHasInteractedWithColor] = useState(false);
  const [showColorInstructionHighlight, setShowColorInstructionHighlight] = useState(false);
  const [colorInstructionKey, setColorInstructionKey] = useState(0);
  const [isMobile, setIsMobile] = useState<boolean>(false);
  const [shareFeedback, setShareFeedback] = useState<string>('');
  const [copyUrlFeedback, setCopyUrlFeedback] = useState<string>('');
  const [wizardVisible, setWizardVisible] = useState(false); // Ensure this is present
  const [shouldScrollToWizard, setShouldScrollToWizard] = useState<boolean>(false); // For scroll timing

  // State for wizard completion
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  const [isResultsStepCompleted, setIsResultsStepCompleted] = useState(false);
  const [generatedExtendedId, setGeneratedExtendedId] = useState<string | null>(null);
  const [currentExampleCardIndex, setCurrentExampleCardIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);
  const [swipeDeltaX, setSwipeDeltaX] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  
  const [pressedButtonIndex, setPressedButtonIndex] = useState<number | null>(null);
  const [mouseIsDown, setMouseIsDown] = useState(false);
  
  const [primaryImage, setPrimaryImage] = useState<{ src: string; animationClass: string }>({ src: '', animationClass: '' });
  const [secondaryImage, setSecondaryImage] = useState<{ src: string | null; animationClass: string; initialTranslate: string }>({ src: null, animationClass: '', initialTranslate: '' });
  
  const [isHeroCardFlipped, setIsHeroCardFlipped] = useState(false);
  const [heroCardSwipeDirection, setHeroCardSwipeDirection] = useState<'left' | 'right' | null>(null);
  const [heroFlipCount, setHeroFlipCount] = useState<number>(0);

  const heroImageContainerRef = useRef<HTMLDivElement>(null);
  const [currentDbId, setCurrentDbId] = useState<number | null>(null);
  
  // Image dimensions for step 2
  const [cropImageDimensions, setCropImageDimensions] = useState<{ width: number; height: number } | null>(null);
  
  const [typedLines, setTypedLines] = useState<string[]>([]);
  const typingLogicRef = useRef<{
    intervalId: NodeJS.Timeout | null;
    lineIdx: number;
    charIdx: number;
    delayCounter: number;
    isWaitingForNewLineDelay: boolean;
  }>({
    intervalId: null,
    lineIdx: 0,
    charIdx: 0,
    delayCounter: 0,
    isWaitingForNewLineDelay: false,
  });
  
  const [heroCardsLoading, setHeroCardsLoading] = useState<boolean>(true);
  const [fetchedHeroCards, setFetchedHeroCards] = useState<Array<{ id: string; v: string | null; h: string | null; bv: string | null; bh: string | null }>>([]);

  const [noteText, setNoteText] = useState<string>("");
  const [isNoteStepActive, setIsNoteStepActive] = useState<boolean>(false);
  const [isSubmittingNote, setIsSubmittingNote] = useState<boolean>(false);
  const [noteSubmissionError, setNoteSubmissionError] = useState<string | null>(null);

  const [photoDate, setPhotoDate] = useState<string | null>(null);
  const [photoLatitude, setPhotoLatitude] = useState<number | null>(null);
  const [photoLongitude, setPhotoLongitude] = useState<number | null>(null);
  const [photoLocationCountry, setPhotoLocationCountry] = useState<string | null>(null);

  const mainContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null); // Ensure this is present
  const wizardSectionRef = useRef<HTMLDivElement>(null); // Ref for the wizard section
  const hiddenFileInputRef = useRef<HTMLInputElement>(null); // Always-present hidden file input

  const internalApiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY;
  const [pendingExampleCardIndex, setPendingExampleCardIndex] = useState<number | null>(null);

  const extractExifData = async (file: File): Promise<{
    date: string | null;
    latitude: number | null;
    longitude: number | null;
    country: string | null;
  }> => {
    try {
      console.log(`[EXIF] Starting EXIF extraction for file: ${file.name}`);
      
      // Dynamic import to avoid SSR issues and reduce bundle warnings
      const { parse } = await import('exifr');
      
      const exifData = await parse(file, {
        gps: true, exif: true, tiff: true, icc: false, iptc: false, jfif: false, ihdr: false
      });
      console.log('[EXIF] Raw EXIF data:', exifData);
      let date: string | null = null;
      let latitude: number | null = null;
      let longitude: number | null = null;
      let country: string | null = null;
      if (exifData?.DateTimeOriginal) {
        const dateObj = new Date(exifData.DateTimeOriginal);
        if (!isNaN(dateObj.getTime())) {
          date = dateObj.toISOString().split('T')[0].replace(/-/g, '/');
          console.log(`[EXIF] Extracted date: ${date}`);
        }
      } else if (exifData?.DateTime) {
        const dateObj = new Date(exifData.DateTime);
        if (!isNaN(dateObj.getTime())) {
          date = dateObj.toISOString().split('T')[0].replace(/-/g, '/');
          console.log(`[EXIF] Extracted date from DateTime: ${date}`);
        }
      }
      if (exifData?.latitude && exifData?.longitude) {
        latitude = exifData.latitude;
        longitude = exifData.longitude;
        console.log(`[EXIF] Extracted GPS: ${latitude}, ${longitude}`);
        try {
          if (latitude !== null && longitude !== null) {
            country = await reverseGeocode(latitude, longitude);
            console.log(`[EXIF] Reverse geocoded country: ${country}`);
          }
        } catch (geoError) {
          console.warn('[EXIF] Reverse geocoding failed:', geoError);
        }
      } else {
        console.log('[EXIF] No GPS coordinates found in EXIF data');
      }
      return { date, latitude, longitude, country };
    } catch (error) {
      console.warn('[EXIF] Failed to extract EXIF data:', error);
      return { date: null, latitude: null, longitude: null, country: null };
    }
  };

  const reverseGeocode = async (lat: number, lon: number): Promise<string | null> => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=3&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'shadefreude-app', // Required by Nominatim usage policy
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Nominatim API returned ${response.status}`);
      }

      const data = await response.json();
      const country = data?.address?.country || data?.display_name?.split(',')?.pop()?.trim();
      
      return country || null;
    } catch (error) {
      console.warn('[EXIF] Reverse geocoding error:', error);
      return null;
    }
  };

  // Helper to restore page scroll on mobile
  const restorePageScroll = () => {
    if (isMobile) {
      document.body.style.overflow = '';
    }
  };



  // Effect to reset overflow on hero image container after flip animation
  useEffect(() => {
    let timeoutId: NodeJS.Timeout | undefined = undefined;

    // This effect runs after isHeroCardFlipped has changed.
    // handleHeroCardFlip would have just set overflow to 'visible' if a flip was initiated.
    // We always want to set it back to 'hidden' after the animation duration.

    if (heroImageContainerRef.current && heroImageContainerRef.current.style.overflow === 'visible') {
      // If overflow is visible, it means a flip was likely just initiated.
      // Start a timer to set it back to hidden after the animation.
      timeoutId = setTimeout(() => {
        if (heroImageContainerRef.current) {
          heroImageContainerRef.current.style.overflow = 'hidden';
        }
      }, 800); // Match CSS flip animation duration (0.8s)
    } else if (heroImageContainerRef.current && !isHeroCardFlipped && heroImageContainerRef.current.style.overflow !== 'hidden') {
      // This is a fallback: if the card is front-facing (e.g., initial load, or flipped back to front and timeout was cleared early)
      // and overflow is not already hidden, hide it.
      // This helps ensure the default state for the front-facing card is overflow: hidden.
      heroImageContainerRef.current.style.overflow = 'hidden';
    }

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isHeroCardFlipped]); // Re-run when flip state changes

  // Scroll to the active step or results
  useEffect(() => {
    if (currentWizardStep === 'results') {
      resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [currentWizardStep]);

  // Detect if user is on mobile
  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // standard breakpoint for mobile
    };

    checkIfMobile();
    window.addEventListener('resize', checkIfMobile);

    return () => {
      window.removeEventListener('resize', checkIfMobile);
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    
    const loadHeroCards = async () => {
      if (HERO_EXAMPLE_CARD_EXTENDED_IDS.length === 0) {
        setHeroCardsLoading(false);
        setFetchedHeroCards([]);
        return;
      }
      
      setHeroCardsLoading(true);
      console.log('[Hero Cards] Loading from cache...');
      
      try {
        // Try to load from local cache first
        const manifestResponse = await fetch('/hero-cache/manifest.json');
        
        if (manifestResponse.ok) {
          const manifest = await manifestResponse.json();
          console.log('[Hero Cards] Using cached manifest');
          
          if (isMounted) {
            // Transform manifest to expected format, maintaining order
            const orderedCards = HERO_EXAMPLE_CARD_EXTENDED_IDS
              .map(extendedId => manifest[extendedId])
              .filter(card => card !== null && card !== undefined && (card.v || card.h));

            console.log('[Hero Cards] Loaded', orderedCards.length, 'cards from cache');
            
            setFetchedHeroCards(orderedCards);
            setHeroCardsLoading(false);
          }
        } else {
          // Fallback to API if cache not available
          console.log('[Hero Cards] Cache not available, falling back to API');
          await fetchHeroCardsFromAPI();
        }
      } catch (error) {
        console.error('[Hero Cards] Cache load failed, falling back to API:', error);
        if (isMounted) {
          await fetchHeroCardsFromAPI();
        }
      }
    };

    const fetchHeroCardsFromAPI = async () => {
      try {
        const response = await fetch('/api/batch-retrieve-cards', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ extended_ids: HERO_EXAMPLE_CARD_EXTENDED_IDS }),
        });

        if (!response.ok) {
          throw new Error(`API fetch failed: ${response.status}`);
        }

        const batchResult = await response.json();
        console.log('[Hero Cards] API fetch completed');

        if (isMounted) {
          const orderedCards = HERO_EXAMPLE_CARD_EXTENDED_IDS
            .map(extendedId => batchResult.cards[extendedId])
            .filter(card => card !== null && card !== undefined && (card.v || card.h));

          console.log('[Hero Cards] Processed', orderedCards.length, 'cards from API');
          
          setFetchedHeroCards(orderedCards);
          setHeroCardsLoading(false);
        }
      } catch (error) {
        console.error('[Hero Cards] API fetch failed:', error);
        if (isMounted) {
          setFetchedHeroCards([]);
          setHeroCardsLoading(false);
        }
      }
    };

    loadHeroCards();
    return () => { isMounted = false; };
  }, []);

  // Initialize primaryImage based on initial currentExampleCardIndex, isMobile, and fetchedHeroCards
  useEffect(() => {
    if (!heroCardsLoading && fetchedHeroCards.length > 0) {
      const card = fetchedHeroCards[currentExampleCardIndex];
      if (card) {
        const initialImageSrc = isMobile ? card.v || card.h : card.h || card.v;
        if (initialImageSrc) {
          setPrimaryImage({ src: initialImageSrc, animationClass: '' });
          console.log("[Hero Init] Initial primaryImage.src set to:", initialImageSrc);
        } else {
          console.warn(`[Hero Init] Card at index ${currentExampleCardIndex} has no image URLs.`);
          setPrimaryImage({ src: '/placeholder-hero.png', animationClass: '' }); // Fallback placeholder
        }
      } else {
        console.warn(`[Hero Init] No card data found at currentExampleCardIndex: ${currentExampleCardIndex} after loading.`);
        setPrimaryImage({ src: '/placeholder-hero.png', animationClass: '' }); // Fallback placeholder
      }
    } else if (!heroCardsLoading && fetchedHeroCards.length === 0 && HERO_EXAMPLE_CARD_EXTENDED_IDS.length > 0) {
        console.warn("[Hero Init] Hero cards were fetched, but the resulting array is empty or all items filtered out.");
        setPrimaryImage({ src: '/placeholder-hero.png', animationClass: '' }); // Fallback placeholder
    }
  }, [currentExampleCardIndex, isMobile, fetchedHeroCards, heroCardsLoading]);

  useEffect(() => {
    const logic = typingLogicRef.current;

    if (isGenerating) {
      setTypedLines(DUMMY_MESSAGES.length > 0 ? [""] : []); // Start with an empty string for the first line
      logic.lineIdx = 0;
      logic.charIdx = 0;
      logic.delayCounter = 0;
      logic.isWaitingForNewLineDelay = false; // First line starts immediately

      if (DUMMY_MESSAGES.length === 0) return;

      logic.intervalId = setInterval(() => {
        if (logic.lineIdx >= DUMMY_MESSAGES.length) {
          if (logic.intervalId) clearInterval(logic.intervalId);
          return;
        }

        if (logic.isWaitingForNewLineDelay) {
          logic.delayCounter++;
          if (logic.delayCounter >= NEW_LINE_DELAY_TICKS) {
            logic.isWaitingForNewLineDelay = false;
            logic.delayCounter = 0;
            setTypedLines(prev => { // Ensure new line container exists
              const next = [...prev];
              if (next.length <= logic.lineIdx) next.push("");
              return next;
            });
          } else {
            setTypedLines(prev => { // Ensure new line container exists for cursor
              const next = [...prev];
              if (next.length <= logic.lineIdx && logic.lineIdx < DUMMY_MESSAGES.length) {
                  next.push("");
              }
              return next;
            });
            return; 
          }
        }

        const currentTargetLine = DUMMY_MESSAGES[logic.lineIdx];
        if (logic.charIdx < currentTargetLine.length) {
          setTypedLines(prevLines => {
            const newLines = [...prevLines];
            newLines[logic.lineIdx] = currentTargetLine.substring(0, logic.charIdx + 1);
            return newLines;
          });
          logic.charIdx++;
        } else {
          logic.lineIdx++; 
          logic.charIdx = 0; 

          if (logic.lineIdx < DUMMY_MESSAGES.length) {
            logic.isWaitingForNewLineDelay = true; 
            logic.delayCounter = 0;
            setTypedLines(prevLines => [...prevLines, ""]); // Add container for next line
          } else {
            if (logic.intervalId) clearInterval(logic.intervalId);
          }
        }
      }, CHAR_TYPING_SPEED_MS);

    } else { 
      if (logic.intervalId) {
        clearInterval(logic.intervalId);
        logic.intervalId = null;
      }
    }

    return () => { 
      if (logic.intervalId) {
        clearInterval(logic.intervalId);
      }
    };
  }, [isGenerating]);

  const resetWizard = () => {
    setUploadStepPreviewUrl(null);
    setCroppedImageDataUrl(null);
    setSelectedHexColor('#000000');
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    setGeneratedExtendedId(null);
    setCurrentDisplayOrientation('horizontal');
    setIsGenerating(false);
    setGenerationError(null);
    setColorNameInput('');
    setGenerationProgress(0);
    setSelectedFileName(null);
    setUserHasInteractedWithColor(false);

    setCurrentWizardStep('upload');
    setIsUploadStepCompleted(false);
    setIsCropStepCompleted(false);
    setIsColorStepCompleted(false);
    setIsResultsStepCompleted(false);
    
    // Reset note states as well
    setNoteText("");
    setCurrentDbId(null);
    setIsNoteStepActive(false);
    setIsSubmittingNote(false);
    setNoteSubmissionError(null);

    // Reset EXIF data
    setPhotoDate(null);
    setPhotoLatitude(null);
    setPhotoLongitude(null);
    setPhotoLocationCountry(null);

    // Reset crop image dimensions
    setCropImageDimensions(null);

    // Revoke URLs
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    console.log('Wizard reset.');

    // Reset animation states
    setIsAnimating(false);
    setPrimaryImage({ src: primaryImage.src, animationClass: '' });
    setSecondaryImage({ src: null, animationClass: '', initialTranslate: '' });

    // Reset wizard visibility
    setWizardVisible(false);
  };

  const handleImageSelectedForUpload = (file: File) => {
    // If called from the new button flow, wizardVisible is false.
    // If called from within an already visible wizard (e.g. user clicks step 1 again), wizardVisible is true.

    if (!wizardVisible) { // Coming from the new "Create Your Card" button flow
        setUploadStepPreviewUrl(null);
        setCroppedImageDataUrl(null);
        setGeneratedVerticalImageUrl(null);
        setGeneratedHorizontalImageUrl(null);
        setGeneratedExtendedId(null);
        setIsGenerating(false);
        setGenerationError(null);
        setGenerationProgress(0);
        setSelectedFileName(null);
        setIsUploadStepCompleted(false); 
        setIsCropStepCompleted(false);
        setIsColorStepCompleted(false);
        setIsResultsStepCompleted(false);
        setNoteText("");
        setCurrentDbId(null);
        setIsNoteStepActive(false);
        setPhotoDate(null);
        setPhotoLatitude(null);
        setPhotoLongitude(null);
        setPhotoLocationCountry(null);
        setCropImageDimensions(null);
        setCurrentWizardStep('upload'); // Ensure it's reset for the new flow
    } else { // User is re-uploading from within the wizard
        // Minimal reset for re-upload:
        setCroppedImageDataUrl(null);
        setGeneratedVerticalImageUrl(null);
        setGeneratedHorizontalImageUrl(null);
        setGeneratedExtendedId(null);
        setIsGenerating(false);
        setGenerationError(null);
        setGenerationProgress(0);
        setIsCropStepCompleted(false);
        setIsColorStepCompleted(false);
        setIsResultsStepCompleted(false);
        setCropImageDimensions(null);
        setCurrentWizardStep('upload'); 
    }

    console.log(`STEP 1.1: Original file selected - Name: ${file.name}, Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`);
    setSelectedFileName(file.name);
    
    // Extract EXIF data in the background
    extractExifData(file).then(({ date, latitude, longitude, country }) => {
      console.log(`[EXIF] Extracted data - Date: ${date}, GPS: ${latitude}, ${longitude}, Country: ${country}`);
      setPhotoDate(date);
      setPhotoLatitude(latitude);
      setPhotoLongitude(longitude);
      setPhotoLocationCountry(country);
    }).catch(error => {
      console.warn('[EXIF] EXIF extraction failed:', error);
      // Don't fail the upload if EXIF extraction fails
    });
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      setUploadStepPreviewUrl(dataUrl);
      setIsUploadStepCompleted(true);
      setCurrentWizardStep('crop'); // Move to next step
      setWizardVisible(true); 
      setShouldScrollToWizard(true); // New: trigger scroll via useEffect
    };
    reader.onerror = () => {
      console.error('Error reading file for preview.');
      setGenerationError('Error reading file for preview.');
      resetWizard(); // Reset if file reading fails
    };
    reader.readAsDataURL(file);
  };

  // New useEffect for scrolling to wizard when shouldScrollToWizard becomes true
  useEffect(() => {
    if (shouldScrollToWizard && wizardVisible && wizardSectionRef.current) {
      // More aggressive scroll approach
      const element = wizardSectionRef.current;
      const elementTop = element.offsetTop;
      const offset = 20; // Small offset from the very top
      
      window.scrollTo({
        top: elementTop - offset,
        behavior: 'smooth'
      });
      
      setShouldScrollToWizard(false); // Reset the trigger
    }
  }, [shouldScrollToWizard, wizardVisible]);

  // Make sure this matches the same ratio as in the backend (square for better card display)
  const aspectRatio = 1/1; // 1:1 ratio (square) for better alignment with the card layout

  const handleCroppedImage = (dataUrl: string | null) => {
    setCroppedImageDataUrl(dataUrl);
    // When image is cropped, reset subsequent steps' progress
    setIsColorStepCompleted(false);
    setIsResultsStepCompleted(false);
    setUserHasInteractedWithColor(false); 
    setSelectedHexColor('#000000');
    setGeneratedVerticalImageUrl(null); 
    setGeneratedHorizontalImageUrl(null);

    if (dataUrl) {
      setIsCropStepCompleted(true);
      setCurrentWizardStep('color');
    } else {
      setIsCropStepCompleted(false); // If crop is cleared, mark as not completed
      setCurrentWizardStep('crop'); // Stay on crop step or move back
    }
  };



  const handleImageDimensionsChange = (dimensions: { width: number; height: number } | null) => {
    setCropImageDimensions(dimensions);
  };

  const handleHexColorChange = (hex: string) => {
    setSelectedHexColor(hex);
    setUserHasInteractedWithColor(true);
     // Reset generation if color changes after generation
    if (isColorStepCompleted) {
        setGeneratedVerticalImageUrl(null);
        setGeneratedHorizontalImageUrl(null);
        setIsColorStepCompleted(false); // Require re-generation
        setIsResultsStepCompleted(false);
        setCurrentWizardStep('color'); // Stay to regenerate
    }
  };

  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor || !userHasInteractedWithColor) {
      setGenerationError('Please ensure an image is cropped and a color has been actively selected.');
      if (!userHasInteractedWithColor) {
        setShowColorInstructionHighlight(true);
        setColorInstructionKey(prev => prev + 1);
        setTimeout(() => setShowColorInstructionHighlight(false), 3000);
      }
      return;
    }
    if (isGenerating) return;

    // Mark step 3 as completed immediately when generation starts
    setIsColorStepCompleted(true); 

    // Reset the results state before generating new images
    setIsResultsStepCompleted(false);
    setIsGenerating(true);
    setGenerationError(null);
    // setGenerationProgress(0); // Initial progress for the first API call - REMOVE for timer
    
    // Immediately move to step 4 (results) to show progress bar there
    setCurrentWizardStep('results');
    
    // On mobile, scroll to step 4 immediately to prevent jumping to top
    if (isMobile) {
      setTimeout(() => {
        wizardSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
    
    // Clear previous images before new generation
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);

    // ---- START: Restore smooth progress bar ----
    setGenerationProgress(0); // Reset progress before starting
    const totalProgressDuration = 60000; // 30 seconds in milliseconds (adjust as needed)
    const updatesPerSecond = 10;
    const progressIntervalTime = 1000 / updatesPerSecond;
    const totalUpdates = totalProgressDuration / progressIntervalTime;
    const progressIncrement = 100 / totalUpdates;
    let currentProgressValue = 0;

    const progressInterval = setInterval(() => {
      currentProgressValue += progressIncrement;
      const newProgress = Math.min(100, currentProgressValue);
      setGenerationProgress(newProgress);

      if (newProgress >= 100) {
        clearInterval(progressInterval);
      }
    }, progressIntervalTime);
    // ---- END: Restore smooth progress bar ----
    
    if (!internalApiKey) {
      console.error('Internal API Key is not defined in frontend environment variables.');
      setGenerationError('Client-side configuration error: API key missing.');
      setIsGenerating(false);
      setCurrentWizardStep('color');
      return;
    }

    let dbId: number | null = null;

    try {
      // STEP 1: Initiate Card Generation
      // setGenerationProgress(10); // REMOVE discrete progress update
      console.log('Frontend: Initiating card generation with hex:', selectedHexColor);

      const initiateResponse = await fetch('/api/initiate-card-generation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Internal-API-Key': internalApiKey,
        },
        body: JSON.stringify({
          hex_color: selectedHexColor,
        }),
      });

      const initiateResult = await initiateResponse.json();
      if (!initiateResponse.ok) {
        throw new Error(initiateResult.detail || `Failed to initiate card generation: ${initiateResponse.status}`);
      }
      
      dbId = initiateResult.db_id;
      const extendedIdFromServer = initiateResult.extended_id;
      setGeneratedExtendedId(extendedIdFromServer);
      setCurrentDbId(dbId);
      console.log(`Frontend: Initiation successful. DB ID: ${dbId}, Extended ID: ${extendedIdFromServer}`);
      // setGenerationProgress(30); // REMOVE discrete progress update

      // Convert base64 Data URL to Blob for multipart/form-data upload
      const fetchRes = await fetch(croppedImageDataUrl!);
      const blob = await fetchRes.blob();
      const imageFile = new File([blob], selectedFileName || 'user_image.png', { type: blob.type });

      // STEP 2: Finalize Card Generation
      const cardNameToSend = colorNameInput.trim() === '' ? 'Untitled Shade' : colorNameInput;
      console.log(`Frontend: Finalizing card generation for DB ID: ${dbId} with name: ${cardNameToSend}`);
      const formData = new FormData();
      formData.append('user_image', imageFile);
      formData.append('card_name', cardNameToSend);

      // Add EXIF data as form fields if available
      if (photoDate) {
        formData.append('photo_date', photoDate);
        console.log(`[EXIF] Adding photo_date to form: ${photoDate}`);
      }
      if (photoLocationCountry) {
        formData.append('photo_location', photoLocationCountry);
        console.log(`[EXIF] Adding photo_location to form: ${photoLocationCountry}`);
      }
      if (photoLatitude !== null && photoLongitude !== null) {
        formData.append('photo_latitude', photoLatitude.toString());
        formData.append('photo_longitude', photoLongitude.toString());
        console.log(`[EXIF] Adding coordinates to form: ${photoLatitude}, ${photoLongitude}`);
      }
      // Note: Sending both country and coordinates for complete location data

      const finalizeResponse = await fetch(`/api/finalize-card-generation/${dbId}`, {
        method: 'POST',
        headers: {
          // Content-Type is set automatically by FormData
          'X-Internal-API-Key': internalApiKey,
        },
        body: formData,
      });
      
      // setGenerationProgress(70); // REMOVE discrete progress update

      // console.log('Frontend: Finalization call successful.'); // DEBUG REMOVED
      
      // Check for non-OK response before trying to parse JSON
      if (!finalizeResponse.ok) {
        let errorDetail = `Failed to finalize card generation: ${finalizeResponse.status}`;
        try {
          const errorResult = await finalizeResponse.json();
          // Attempt to get a more specific message from FastAPI validation errors
          if (errorResult.detail && Array.isArray(errorResult.detail) && errorResult.detail[0] && errorResult.detail[0].msg) {
            errorDetail = errorResult.detail[0].msg;
          } else if (typeof errorResult.detail === 'string') {
            errorDetail = errorResult.detail;
          } // else stick with the status code error or errorResult itself if it's a plain string
        } catch (parseError) {
          console.warn('Could not parse error response JSON:', parseError);
        }
        const error = new Error(errorDetail);
        (error as any).status = finalizeResponse.status; // Attach status to error object
        throw error;
      }
      
      const finalizeResult = await finalizeResponse.json();
      // console.log('Frontend: Parsed finalizeResult:', JSON.stringify(finalizeResult, null, 2)); // DEBUG REMOVED

      const horizontalUrl = finalizeResult.front_horizontal_image_url;
      const verticalUrl = finalizeResult.front_vertical_image_url;
      // console.log('Frontend: Extracted horizontalUrl:', horizontalUrl); // DEBUG REMOVED
      // console.log('Frontend: Extracted verticalUrl:', verticalUrl); // DEBUG REMOVED

      if (!horizontalUrl && !verticalUrl) {
        throw new Error('API returned success but no image URLs were found in the response.');
      }
      
      // AI color name update logic was here, now fully removed.

      setGeneratedHorizontalImageUrl(horizontalUrl || null);
      setGeneratedVerticalImageUrl(verticalUrl || null);
      
      setIsColorStepCompleted(true);
      // setCurrentWizardStep('results'); // Already on results step
      setIsResultsStepCompleted(true);
      // console.log('Frontend: State updated for results step. currentWizardStep:', 'results'); // DEBUG REMOVED
      
      // Determine initial display orientation and target image for preloading
      let initialDisplayUrl: string | null = null;
      let initialOrientation: 'horizontal' | 'vertical';

      if (isMobile && verticalUrl) {
        initialOrientation = 'vertical';
        initialDisplayUrl = verticalUrl;
      } else if (horizontalUrl) {
        initialOrientation = 'horizontal';
        initialDisplayUrl = horizontalUrl;
      } else if (verticalUrl) { // Fallback if only vertical is available (non-mobile)
        initialOrientation = 'vertical';
        initialDisplayUrl = verticalUrl;
      } else {
        initialOrientation = 'horizontal'; // Default if somehow no URLs (though we check above)
      }
      setCurrentDisplayOrientation(initialOrientation);

      // Preload the initially displayed image and scroll after it loads (desktop only)
      if (initialDisplayUrl && !isMobile) {
        const img = new Image();
        img.onload = () => {
          console.log('Frontend: Initial image loaded, scrolling to controls.');
          cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };
        img.onerror = () => {
          console.warn('Frontend: Initial image failed to preload, scrolling anyway.');
          cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };
        img.src = initialDisplayUrl;
      } else if (!isMobile) {
        // If no specific image to preload (should not happen if URLs are present),
        // scroll immediately (or with a small delay as a fallback) - desktop only
        setTimeout(() => {
            cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        },100);
      }

      // setGenerationProgress(100); // REMOVE discrete progress update, handled by interval or finally block
      clearInterval(progressInterval); // Ensure interval is cleared on successful completion
      setGenerationProgress(100); // Explicitly set to 100 on success
      
      // Activate the note input step instead of immediately redirecting
      setIsNoteStepActive(true);
      
      // On mobile, ensure we stay at the wizard section, don't scroll to card controls
      if (isMobile) {
        // Small delay to ensure state updates are complete
        setTimeout(() => {
          wizardSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 200);
      } else {
        // Desktop: scroll to card display controls
        cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      } 

    } catch (error) {
      // Ensure we log a string message from the error object for console
      let consoleErrorMessage = 'Unknown error during image generation';
      if (error instanceof Error) {
        consoleErrorMessage = error.message;
      } else if (typeof error === 'string') {
        consoleErrorMessage = error;
      } else if (typeof error === 'object' && error !== null && (error as any).message) {
        consoleErrorMessage = (error as any).message;
      } else if (typeof error === 'object' && error !== null) {
        try {
            consoleErrorMessage = JSON.stringify(error);
        } catch { /* ignore stringify error */ }
      }
      console.error(`Frontend: Error during image generation process: -- ${consoleErrorMessage}`, error); // Log the original error object too for full context
      
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
      // For ANY error during the actual generation attempt (initiate or finalize)
      // stay on the 'results' step and show an error + retry option.
      setGenerationError(errorMessage);
      setGeneratedHorizontalImageUrl(null); 
      setGeneratedVerticalImageUrl(null);
      // Do NOT change currentWizardStep here, stay on 'results'
      // Do NOT change isColorStepCompleted here

      // The API key check earlier has its own reset to 'color' step.
      // Only log dbId warning if it's not a handled client-side error already.
      if (dbId && !(error instanceof Error && (error as any).status === 408)) { // Example: don't repeat for already specific 408 log.
        // This console warning might need refinement based on what errors we expect to handle gracefully vs. what are true backend issues.
        console.warn(`Generation process failed after initiating with DB ID: ${dbId}. Error: ${errorMessage}`);
      }
      clearInterval(progressInterval); // Clear interval on error
    } finally {
      setIsGenerating(false);
      // Ensure progress is 100 and interval is cleared, regardless of outcome
      if (currentProgressValue < 100) { // Check if interval might still be running
        clearInterval(progressInterval);
      }
      setGenerationProgress(100); 
    }
  };

  const setStep = (step: WizardStepName) => {
    // If clicking the current step, don't change it (let WizardStep handle collapsing)
    if (step === currentWizardStep) {
      return;
    }
    
    // Basic forward navigation only if prerequisites met
    if (step === 'upload') setCurrentWizardStep('upload');
    else if (step === 'crop' && isUploadStepCompleted) setCurrentWizardStep('crop');
    else if (step === 'color' && isCropStepCompleted) setCurrentWizardStep('color');
    else if (step === 'results' && isColorStepCompleted) setCurrentWizardStep('results');
  };
  
  // Helper to determine if a step header should be clickable (i.e., it's a past, completed step)
  const isStepHeaderClickable = (stepName: WizardStepName): boolean => {
    if (stepName === 'upload' && (isUploadStepCompleted || currentWizardStep === 'upload')) return true;
    if (stepName === 'crop' && (isCropStepCompleted || (currentWizardStep === 'crop' && isUploadStepCompleted))) return true;
    if (stepName === 'color' && (isColorStepCompleted || (currentWizardStep === 'color' && isCropStepCompleted))) return true;
    // Allow returning to results if generating, or if results are completed, or if currently on results and color step was done.
    if (stepName === 'results' && (isGenerating || isResultsStepCompleted || (currentWizardStep === 'results' && isColorStepCompleted))) return true;
    return false;
  };

  const handleDownloadImage = (orientation: 'vertical' | 'horizontal' = 'vertical') => {
    const imageUrl = orientation === 'vertical' ? generatedVerticalImageUrl : generatedHorizontalImageUrl;
    if (!imageUrl) return;

    // Construct the filename as before
    const filename = `shadefreude-${orientation}-${selectedHexColor.substring(1)}-${new Date().getTime()}.png`;

    // Construct the URL to the new API endpoint
    const downloadUrl = `/api/download-image?url=${encodeURIComponent(imageUrl)}&filename=${encodeURIComponent(filename)}`;

    // Trigger the download by navigating to the API endpoint
    // The browser will handle the download prompt because of the Content-Disposition header set by the API
    window.location.href = downloadUrl;
  };

  const handleShare = async () => {
    const currentImageUrl = currentDisplayOrientation === 'horizontal' ? generatedHorizontalImageUrl : generatedVerticalImageUrl;
    if (!currentImageUrl) {
      setShareFeedback('No image to share.');
      setTimeout(() => setShareFeedback(''), 2000);
      return;
    }

    let shareUrl = currentImageUrl; // Default to direct image URL
    if (generatedExtendedId) {
      const slug = generatedExtendedId.replace(/\s+/g, '-').toLowerCase();
      shareUrl = `https://sf.tinker.institute/color/${slug}`;
    }
    
    const shareMessage = `My latest shadefreude discovery – a color with a tale to tell: ${shareUrl}`;

    const shareData = {
      title: 'shadefreude Color Card',
      text: shareMessage,
      url: shareUrl, 
    };

    await shareOrCopy(shareData, shareMessage, {
        onShareSuccess: (message: string) => setShareFeedback(message),
        onCopySuccess: (message: string) => setShareFeedback(message),
        onShareError: (message: string) => setShareFeedback(message),
        onCopyError: (message: string) => setShareFeedback(message),
        shareSuccessMessage: 'Shared successfully!',
        copySuccessMessage: 'Share message with image link copied to clipboard!',
        shareErrorMessage: 'Sharing failed. Try copying the link.',
    });

    setTimeout(() => setShareFeedback(''), 3000);
    setCopyUrlFeedback(''); // Clear copy feedback if share is used
  };

  const handleCopyGeneratedUrl = async () => {
    if (!generatedExtendedId) {
      setCopyUrlFeedback('Cannot copy URL: Card not yet fully generated.');
      setTimeout(() => setCopyUrlFeedback(''), 3000);
      return;
    }
    const slug = generatedExtendedId.replace(/\s+/g, '-').toLowerCase();
    const urlToCopy = `https://sf.tinker.institute/color/${slug}`;
    
    await copyTextToClipboard(urlToCopy, {
        onSuccess: (message: string) => setCopyUrlFeedback(message),
        onError: (message: string) => setCopyUrlFeedback(message),
        successMessage: COPY_SUCCESS_MESSAGE,
    });

    setTimeout(() => setCopyUrlFeedback(''), 3000);
    setShareFeedback(''); // Clear share feedback if copy is used
  };

  const handleAnimationEnd = () => {
    if (!secondaryImage.src) {
      restorePageScroll();
      return;
    }
    const newPrimarySrc = secondaryImage.src;
    const newCurrentIndex = fetchedHeroCards.findIndex(card => {
      const cardUrl = isMobile ? card.v || card.h : card.h || card.v;
      return cardUrl === newPrimarySrc;
    });
    setPrimaryImage({ src: newPrimarySrc, animationClass: '' });
    setSecondaryImage({ src: null, animationClass: '', initialTranslate: '' });
    setCurrentExampleCardIndex(newCurrentIndex !== -1 ? newCurrentIndex : 0);
    setPendingExampleCardIndex(null); // Clear pending index after animation
    setIsAnimating(false);
    restorePageScroll();
  };

  const triggerImageChangeAnimation = (direction: 'next' | 'prev', targetIndex?: number) => {
    if (isAnimating) return;
    setIsAnimating(true);

    let newIndex: number;
    if (targetIndex !== undefined) {
      newIndex = targetIndex;
    } else {
      if (fetchedHeroCards.length <= 1) {
        setIsAnimating(false);
        return;
      }
      newIndex = direction === 'next'
        ? (currentExampleCardIndex + 1) % fetchedHeroCards.length
        : (currentExampleCardIndex - 1 + fetchedHeroCards.length) % fetchedHeroCards.length;
    }

    const nextCardData = fetchedHeroCards[newIndex];
    if (!nextCardData) {
      console.error(`[Hero Two-Slot] No card data for index ${newIndex}`);
      setIsAnimating(false);
      return;
    }

    const newImageUrl = isMobile ? nextCardData.v || nextCardData.h : nextCardData.h || nextCardData.v;
    if (!newImageUrl) {
      console.error(`[Hero Two-Slot] No image available for card at index ${newIndex}`);
      setIsAnimating(false);
      return;
    }

    // Preload the next image before starting animations
    const img = new Image();
    img.onload = () => {
      if (direction === 'next') { // Swiping UP (next image comes from bottom)
        setSecondaryImage({ 
          src: newImageUrl, 
          animationClass: 'slide-in-from-bottom-animation', 
          initialTranslate: 'translateY(120%)'
        });
        setPrimaryImage(prev => ({ ...prev, animationClass: 'slide-out-to-top-animation' }));
      } else { // Swiping DOWN (next image comes from top)
        setSecondaryImage({ 
          src: newImageUrl, 
          animationClass: 'slide-in-from-top-animation', 
          initialTranslate: 'translateY(-120%)'
        });
        setPrimaryImage(prev => ({ ...prev, animationClass: 'slide-out-to-bottom-animation' }));
      }
      // currentExampleCardIndex will be updated in handleAnimationEnd after animations
    };
    img.onerror = () => {
      console.error(`[Hero Two-Slot] Failed to load image: ${newImageUrl}`);
      setIsAnimating(false); // Reset if image fails to load
    };
    img.src = newImageUrl;
  };

  const handlePageButtonClick = (index: number) => { // Renamed from handleDotClick
    if (isAnimating || index === currentExampleCardIndex) return;
    // Set pending index immediately for instant feedback
    setPendingExampleCardIndex(index);
    // Determine direction for animation (simplistic, could be more robust for wrapping)
    const direction = index > currentExampleCardIndex ? 'next' : 'prev'; 
    triggerImageChangeAnimation(direction, index);
  };

  // New handlers for button press states
  const handleButtonMouseDown = (index: number) => {
    if (isAnimating) return;
    setPressedButtonIndex(index);
    setMouseIsDown(true);
    // Immediately update the selected index for instant visual feedback
    if (index !== currentExampleCardIndex) {
      handlePageButtonClick(index);
    }
  };

  const handleButtonMouseUp = () => {
    setPressedButtonIndex(null);
    setMouseIsDown(false);
  };

  const handleButtonMouseLeave = () => {
    // Clear pressed state if mouse leaves while pressed
    setPressedButtonIndex(null);
    setMouseIsDown(false);
  };

  // New function to handle note submission
  const handleNoteSubmission = async (currentNoteText?: string) => {
    if (!generatedExtendedId || !currentDbId) { // Use currentDbId from state
      setNoteSubmissionError("Card ID not found. Cannot submit note.");
      return;
    }

    setIsSubmittingNote(true);
    setNoteSubmissionError(null);

    try {
      const response = await fetch(`/api/cards/${currentDbId}/add-note`, { // Use currentDbId
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Internal-API-Key': internalApiKey!,
        },
        body: JSON.stringify({ note_text: currentNoteText ? currentNoteText.trim() : null }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || `Failed to submit note: ${response.status}`);
      }

      // Successfully submitted note or skipped
      setIsNoteStepActive(false);
      const slug = result.extended_id?.replace(/\s+/g, '-').toLowerCase() || generatedExtendedId.replace(/\s+/g, '-').toLowerCase();
      
      // Attempt to reset zoom before navigation
      if (document.activeElement && typeof (document.activeElement as HTMLElement).blur === 'function') {
        (document.activeElement as HTMLElement).blur();
      }
      mainContainerRef.current?.focus(); // Focus on a non-input element
      
      // Optional: Short delay if direct focus doesn't work, but can feel clunky
      // await new Promise(resolve => setTimeout(resolve, 50)); 

      router.push(`/color/${slug}`);

    } catch (error) {
      const message = error instanceof Error ? error.message : "An unknown error occurred while submitting the note.";
      setNoteSubmissionError(message);
      console.error("Note submission error:", error);
    } finally {
      setIsSubmittingNote(false);
    }
  };

  const handleHeroCardFlip = (swipeDir: 'left' | 'right' | null = 'right') => {
    if (heroImageContainerRef.current) {
      heroImageContainerRef.current.style.overflow = 'visible'; 
    }
    setHeroCardSwipeDirection(swipeDir);
    setIsHeroCardFlipped(!isHeroCardFlipped);
    setHeroFlipCount(prevCount => prevCount + 1); // ADD THIS LINE
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    if (isAnimating) return; // Prevent action if card is changing (up/down)

    if (isMobile) {
      document.body.style.overflow = 'hidden'; // Disable page scroll
    }

    // For horizontal swipe detection (flipping)
    setTouchStartX(e.touches[0].clientX); 
    // setTouchStartY(e.touches[0].clientY); // Removed for vertical swipe
    setSwipeDeltaX(0);
    // setSwipeDeltaY(0); // Removed for vertical swipe
    // Don't reset primaryImage.animationClass here for flip, it might interfere with vertical swipe snap-back
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (touchStartX === null ) return; // Only proceed if touchStartX is not null (ignore vertical only)
    if (isAnimating && (primaryImage.animationClass.includes('slide') || secondaryImage.animationClass.includes('slide'))) return; // Don't allow swipe if vertical animation is running

    if (touchStartX !== null) {
      const currentX = e.touches[0].clientX;
      setSwipeDeltaX(currentX - touchStartX);
    }
    // Removed logic for swipeDeltaY
    // if (touchStartY !== null) {
    //   const currentY = e.touches[0].clientY;
    //   setSwipeDeltaY(currentY - touchStartY);
    // }
  };

  const handleTouchEnd = (e: React.TouchEvent<HTMLDivElement>) => {
    if (isAnimating && (primaryImage.animationClass.includes('slide') || secondaryImage.animationClass.includes('slide'))) {
      setTouchStartX(null);
      // setTouchStartY(null); // Removed
      restorePageScroll();
      return;
    }

    // Removed: Prioritize vertical swipe for changing cards
    // if (touchStartY !== null && Math.abs(swipeDeltaY) > SWIPE_THRESHOLD && Math.abs(swipeDeltaY) > Math.abs(swipeDeltaX)) {
    //   if (swipeDeltaY < 0) { // Swipe Up
    //     triggerImageChangeAnimation('next');
    //   } else { // Swipe Down
    //     triggerImageChangeAnimation('prev');
    //   }
    //   setHeroCardSwipeDirection(null); // Reset flip direction if vertical swipe occurs
    // } 
    // Horizontal swipe for flipping card
    // else if (touchStartX !== null && Math.abs(swipeDeltaX) > SWIPE_THRESHOLD) {
    if (touchStartX !== null && Math.abs(swipeDeltaX) > SWIPE_THRESHOLD) { // Changed to if from else if
      if (swipeDeltaX < 0) { // Swipe Left
        handleHeroCardFlip('left');
      } else { // Swipe Right
        handleHeroCardFlip('right');
      }
    } 
    // Removed: Snap back for vertical swipe if not enough
    // else if (touchStartY !== null && swipeDeltaY !== 0) { 
    //   setPrimaryImage(prev => ({ ...prev, animationClass: 'snap-back-animation' }));
    // }
    // No snap-back for horizontal, flip is discrete or nothing

    setTouchStartX(null);
    // setTouchStartY(null); // Removed
    
    // swipeDeltaX and swipeDeltaY are reset by animation handlers or if no action taken
    // Only reset swipeDeltaX if no flip action was taken. swipeDeltaY is removed.
    if (!(Math.abs(swipeDeltaX) > SWIPE_THRESHOLD)) {
        setSwipeDeltaX(0);
        // setSwipeDeltaY(0); // Removed
    }
    // Restore page scroll after handling touch end
    restorePageScroll();
  };

  // Auto-flip hero card with different timings
  useEffect(() => {
    let flipInterval: NodeJS.Timeout;

    // Always clear the previous interval when the dependencies change
    // The effect will then set a new interval if conditions are met.
    // Note: clearInterval(undefined) is a no-op, so this is safe even on initial run.
    // We declare flipInterval outside the if block so cleanup can access it.
    const clearCurrentInterval = () => {
      clearInterval(flipInterval);
    };
    clearCurrentInterval(); // Clear any existing interval immediately

    // MODIFIED CONDITION: Check heroFlipCount
    if (fetchedHeroCards.length > 0 && !isAnimating && heroFlipCount < 2) {
      const currentFlipDelay = isHeroCardFlipped ? 3000 : 5000;
      
      flipInterval = setInterval(() => {
        handleHeroCardFlip(); 
      }, currentFlipDelay);
    }

    return () => {
      clearCurrentInterval(); // Clear interval on cleanup
    };
    // Ensure heroFlipCount is in the dependency array
  }, [fetchedHeroCards.length, isAnimating, isHeroCardFlipped, handleHeroCardFlip, heroFlipCount]);

  // New touch cancel handler for the hero card
  const handleHeroCardTouchCancel = (e: React.TouchEvent<HTMLDivElement>) => {
    console.log("Hero card touch cancelled");
    restorePageScroll(); // Ensure scroll is restored on cancel

    // Reset touch states similar to handleTouchEnd
    setTouchStartX(null);
    // setTouchStartY(null); // Removed
    setSwipeDeltaX(0);
    // setSwipeDeltaY(0); // Removed
    
    // isAnimating was primarily for vertical card changes.
    // Horizontal flip animation is CSS-driven and doesn't rely on isAnimating state in the same way.
    // Removing setIsAnimating(false) here to avoid interfering with potential flip animations.
  };

  const handleCreateYourCardClick = () => {
    console.log('handleCreateYourCardClick called');

    // Reset state for the new card flow first
    setUploadStepPreviewUrl(null);
    setCroppedImageDataUrl(null);
    setIsUploadStepCompleted(false);
    setIsCropStepCompleted(false);
    setIsColorStepCompleted(false);
    setIsResultsStepCompleted(false);
    setCurrentWizardStep('upload'); 
    setGenerationError(null);
    setGeneratedExtendedId(null);
    
    // Only trigger file input - don't show wizard yet
    if (hiddenFileInputRef.current) {
      console.log('Triggering hidden file input from handleCreateYourCardClick');
      hiddenFileInputRef.current.value = '';
      hiddenFileInputRef.current.click();
    }
  };

  const handleCreateNewCard = () => {
    console.log('handleCreateNewCard called');
    
    // First reset everything (this will hide the wizard)
    resetWizard();
    
    // Only trigger file input - don't show wizard yet
    setTimeout(() => {
      if (hiddenFileInputRef.current) {
        console.log('Triggering hidden file input from handleCreateNewCard');
        hiddenFileInputRef.current.value = '';
        hiddenFileInputRef.current.click();
      }
    }, 50);
  };

  const handleHiddenFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleImageSelectedForUpload(file);
    }
  };

  return (
    <main ref={mainContainerRef} tabIndex={-1} className="flex min-h-screen flex-col items-center justify-start pt-1 px-4 pb-6 md:pt-3 md:px-4 md:pb-12 bg-background text-foreground focus:outline-none"> {/* Reduced padding from px-6 md:px-12 to px-2 md:px-4 */}
      {/* Hidden file input that's always present */}
      <input
        ref={hiddenFileInputRef}
        type="file"
        accept="image/*"
        onChange={handleHiddenFileInputChange}
        style={{ display: 'none' }}
      />
      <div className="w-full max-w-6xl space-y-4" ref={resultRef}>
        <header className="py-4 border-b-2 border-foreground">
          <h1 className="text-4xl md:text-5xl font-bold text-center flex items-center justify-center">
            <a href="/" onClick={(e) => { e.preventDefault(); resetWizard(); }} className="flex items-center justify-center cursor-pointer">
              <span className="mr-1 ml-1">
                <img src="/sf-icon.png" alt="SF Icon" className="inline h-8 w-8 md:h-12 md:w-12 mr-1" />
                shade
              </span>
              <span className="inline-block bg-card text-foreground border-2 border-blue-700 shadow-[5px_5px_0_0_theme(colors.blue.700)] px-2 py-0.5 mr-1">
                freude
              </span>
            </a>
          </h1>
          <p className="text-center text-sm text-muted-foreground mt-2">
            part of <a href="https://tinker.institute" target="_blank" rel="noopener noreferrer" className="underline hover:text-foreground">tinker.institute</a>
          </p>
        </header>

        {/* Hero Section Text & Example Card */}
        <section className="w-full md:pt-1 md:pb-8 py-3">
          {/* Title and Subtitle - Full Width */}
          <div className="text-left md:text-center mb-4 md:mb-12">
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-2 md:mb-4 text-foreground">
              The Digital Postcard Service
            </h2>
            <p className="text-2xl md:text-3xl lg:text-4xl font-light mb-2 md:mb-4 text-muted-foreground/90 tracking-wide">
              Your everyday photo, having its moment.
            </p>
          </div>

          {/* Two-column layout: Features left, Example card right */}
          <div className="md:grid md:grid-cols-5 md:gap-4 lg:gap-6 md:items-start">
            {/* Left Column: Features & Description - takes 2/5ths */}
            <div className="text-left mb-6 md:mb-0 md:col-span-2 flex flex-col">
              {/* Features */}
              <div className="mb-3 md:mb-4 mt-0 md:mt-6">
                <p className="text-xl md:text-2xl font-light mb-2 md:mb-3 text-muted-foreground/80 tracking-wide">
                  / Polaroid vibes.<br/>/ AI brains.<br/>/ No cringe. Hopefully.
                </p>
              </div>

              {/* Description */}
              <div className="mb-4 md:mb-6">
                <p className="text-md md:text-lg text-muted-foreground leading-relaxed">
                  Pick a color from your photo. Watch it become a <span className="highlight-marker">digital postcard</span> with a custom color name and an observation you didn&apos;t see coming. Each color tells its own story. Add a note on the back if you want. The kind of thing you share, print, or both.
                </p>
              </div>

              {/* Create Your Card Button */}
              <div className="flex justify-center mt-4 md:mt-6">
                <button
                  onClick={handleCreateYourCardClick}
                  className="px-6 py-3 md:px-8 md:py-4 font-semibold md:text-lg bg-black text-white border-2 border-[#374151] shadow-[4px_4px_0_0_#374151] hover:shadow-[2px_2px_0_0_#374151] active:shadow-[1px_1px_0_0_#374151] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center rounded-md"
                >
                  <ImagePlus size={22} className="mr-2" />
                  Create Your Card
                </button>
              </div>
            </div>

            {/* Right Column: Example Card with Navigation - takes 3/5ths */}
            <div className="flex flex-col md:items-center md:justify-center w-full md:col-span-3 relative">
              {/* Wrapper for card image */}
              <div className={`w-full ${isMobile ? 'flex flex-row items-center justify-center' : ''}`}>
                {/* Card Image Container */}
                <div
                  ref={heroImageContainerRef}
                  className={`relative cursor-grab active:cursor-grabbing example-card-image-container md:my-2 mt-2 mb-2 ${isMobile ? 'w-10/12 mx-auto' : 'w-full'}`}
                  style={{
                    aspectRatio: isMobile ? '1/2' : '2/1',
                  }}
                >
                  <div className="w-full h-full perspective-container" onClick={() => { if (!isAnimating && swipeDeltaX === 0) handleHeroCardFlip(); }}>
                    <div 
                      className={`card-flipper w-full h-full ${isHeroCardFlipped ? (heroCardSwipeDirection === 'left' ? 'is-flipped swipe-left' : 'is-flipped swipe-right') : ''}`}
                      onTouchStart={handleTouchStart}
                      onTouchMove={handleTouchMove}
                      onTouchEnd={handleTouchEnd}
                      onTouchCancel={handleHeroCardTouchCancel}
                    >
                      {/* CARD_FRONT and CARD_BACK content */}
                      <div className="card-face card-front">
                        {heroCardsLoading ? (
                          <div className="w-full h-full rounded-lg bg-muted flex items-center justify-center">
                            <p className="text-muted-foreground">Loading examples...</p>
                          </div>
                        ) : primaryImage.src ? (
                          <>
                            <img
                              key={`primary-${primaryImage.src}-${currentExampleCardIndex}`}
                              src={primaryImage.src}
                              alt={`Example shadefreude Card ${currentExampleCardIndex + 1}`}
                              className={`w-full h-full rounded-lg object-contain example-card-image ${primaryImage.animationClass} mx-auto`}
                              style={{
                                zIndex: 10, 
                                position: 'relative',
                                visibility: isHeroCardFlipped ? 'hidden' : 'visible'
                              }}
                              draggable="false"
                              onAnimationEnd={primaryImage.animationClass ? handleAnimationEnd : undefined}
                              onError={(e) => { 
                                  console.error("[Hero Image Error] Failed to load primaryImage.src:", primaryImage.src, e);
                              }}
                            />
                            {secondaryImage.src && !isHeroCardFlipped && ( 
                              <img
                                key={`secondary-${secondaryImage.src}`}
                                src={secondaryImage.src}
                                alt="Next example card image"
                                className={`w-full h-full rounded-lg object-contain example-card-image absolute top-0 left-0 ${secondaryImage.animationClass} mx-auto`}
                                style={{
                                  transform: secondaryImage.initialTranslate,
                                  zIndex: 5,
                                  visibility: isHeroCardFlipped ? 'hidden' : 'visible' 
                                }}
                                draggable="false"
                                onAnimationEnd={secondaryImage.animationClass ? handleAnimationEnd : undefined} 
                              />
                            )}
                          </>
                        ) : (
                          <div className="w-full h-full rounded-lg bg-muted flex items-center justify-center">
                            <p className="text-muted-foreground">No example images available.</p>
                          </div>
                        )}
                      </div>
                      {/* CARD_BACK */} 
                      <div className="card-face card-back rounded-lg overflow-hidden">
                        {(() => {
                          const currentCardData = fetchedHeroCards[currentExampleCardIndex];
                          if (currentCardData) {
                            const backImageUrl = isMobile
                              ? currentCardData.bv || currentCardData.bh
                              : currentCardData.bh || currentCardData.bv;

                            if (backImageUrl) {
                              return <img src={backImageUrl} alt="Hero card back" className="w-full h-full object-contain" />;
                            }
                          }
                          // Fallback if no specific back image for hero card
                          return (
                            <div className="w-full h-full bg-gray-700 text-white flex flex-col items-center justify-center p-4">
                              <p className="text-xl font-semibold">Card Back</p>
                              <p className="text-sm mt-1">(Hero Example - No Specific Back Image)</p>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Numbered Pagination */}
              {HERO_EXAMPLE_CARD_EXTENDED_IDS.length > 1 && (
                <div className="flex justify-center items-center space-x-2 mt-3 mb-1 w-full">
                  {HERO_EXAMPLE_CARD_EXTENDED_IDS.map((_, index) => {
                    const isPressed = ((pendingExampleCardIndex !== null ? pendingExampleCardIndex : currentExampleCardIndex) === index) || (pressedButtonIndex === index && mouseIsDown);
                    const isDisabled = isAnimating || heroCardsLoading || (fetchedHeroCards.length > 0 && index >= fetchedHeroCards.length);
                    
                    return (
                      <button
                        key={`page-btn-${index}`}
                        onMouseDown={() => !isDisabled && handleButtonMouseDown(index)}
                        onMouseUp={handleButtonMouseUp}
                        onMouseLeave={handleButtonMouseLeave}
                        className={`px-3 py-1.5 border-2 border-foreground text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-150
                          ${isDisabled
                            ? 'opacity-50 cursor-not-allowed bg-background text-foreground shadow-[1px_1px_0_0_theme(colors.foreground)]'
                            : isPressed
                            ? 'bg-foreground text-background shadow-none translate-x-[1px] translate-y-[1px]'
                            : 'bg-background text-foreground shadow-[2px_2px_0_0_theme(colors.foreground)] hover:shadow-[3px_3px_0_0_theme(colors.foreground)]'
                          }
                        `}
                        aria-label={`Go to card ${index + 1}`}
                        disabled={isDisabled}
                      >
                        {index + 1}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </section>

        {wizardVisible && (
          <div ref={wizardSectionRef}> {/* REF MOVED HERE - to new parent div for whole wizard section */}
            {/* HR Separator and Title for Wizard Section - now part of the ref'd element */}
            <hr className="w-full border-t-2 border-foreground mt-1 mb-3" />
            <div className="w-full flex flex-col items-start my-2">
              <h2 className="text-2xl md:text-3xl font-bold text-left mt-8 mb-4"><span className="text-lg md:text-xl font-normal text-muted-foreground">create</span> Your card</h2>
            </div>
            
            {/* Container for the wizard steps grid - REF REMOVED FROM HERE */}
            <div className={'grid grid-cols-1 md:grid-cols-1 gap-8 md:gap-4'}>
              <section className="w-full bg-card text-card-foreground border-2 border-foreground space-y-0 flex flex-col">
                <WizardStep 
                  title="1: Take a photo"
                  stepNumber={1} 
                  isActive={currentWizardStep === 'upload'} 
                  isCompleted={isUploadStepCompleted}
                  onHeaderClick={isStepHeaderClickable('upload') ? () => setStep('upload') : undefined}
                >
                  <ImageUpload 
                    ref={fileInputRef}
                    onImageSelect={handleImageSelectedForUpload} 
                    onImageCropped={handleCroppedImage}
                    showUploader={true}
                    showCropper={false}
                    initialPreviewUrl={uploadStepPreviewUrl}
                    currentFileName={selectedFileName}
                    key={`uploader-${selectedFileName}`}
                  />
                </WizardStep>

                {isUploadStepCompleted && (
                <WizardStep 
                  title="2: Frame your focus"
                  stepNumber={2} 
                  isActive={currentWizardStep === 'crop'} 
                  isCompleted={isCropStepCompleted}
                    onHeaderClick={isStepHeaderClickable('crop') ? () => setStep('crop') : undefined}
                >
                    {!isGenerating && (
                      <ImageUpload 
                        onImageSelect={() => {}} // No-op since we're not handling file selection here
                        onImageCropped={handleCroppedImage} 
                        showUploader={false}
                        showCropper={true}
                        initialPreviewUrl={uploadStepPreviewUrl}
                        currentFileName={selectedFileName}
                        aspectRatio={aspectRatio} // Pass the aspect ratio to the cropper
                        onImageDimensionsChange={handleImageDimensionsChange}
                        key={`cropper-${uploadStepPreviewUrl}`}
                      />
                  )}
                </WizardStep>
                )}

                {isCropStepCompleted && (
                <WizardStep 
                  title="3: Pick your signature shade"
                  stepNumber={3} 
                  isActive={currentWizardStep === 'color'} 
                  isCompleted={isColorStepCompleted}
                    onHeaderClick={isStepHeaderClickable('color') ? () => setStep('color') : undefined}
                >
                      <ColorTools 
                        initialHex={selectedHexColor}
                        onHexChange={handleHexColorChange}
                        croppedImageDataUrl={croppedImageDataUrl}
                      onColorPickedFromCanvas={() => {
                        setUserHasInteractedWithColor(true);
                        setShowColorInstructionHighlight(false);
                      }}
                    />
                    <p 
                      key={colorInstructionKey}
                      className={`text-sm text-center mt-4 mb-2 transition-colors duration-300 ${
                        showColorInstructionHighlight ? 'text-red-500 font-medium shake-animation' : 'text-muted-foreground'
                      }`}
                    >
                      Click on the image to pick the color.
                    </p>
                    <div className="flex justify-center w-full gap-4 mt-2">
                      <button
                        type="button"
                        onClick={handleGenerateImageClick}
                        className={`px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 
                            ${(!croppedImageDataUrl || !selectedHexColor || !userHasInteractedWithColor || isGenerating) ? 
                              'opacity-60 cursor-not-allowed shadow-none text-muted-foreground border-muted-foreground' : 
                              '' // Active styles (already part of the base string)
                            }`}
                        >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/><path d="M5 6v4"/><path d="M19 14v4"/><path d="M10 2v2"/><path d="M7 8H3"/><path d="M21 16h-4"/></svg>
                        {isGenerating ? 'Working the magic...' : 'Reveal Its Story'}
                      </button>
                    </div>
                  </WizardStep>
                )}

                {(isCropStepCompleted && ((currentWizardStep === 'results' || isGenerating) || isResultsStepCompleted)) && (
                  <WizardStep
                    title="4: Your card takes form..."
                    stepNumber={4}
                    isActive={currentWizardStep === 'results'}
                    isCompleted={isResultsStepCompleted}
                    onHeaderClick={isStepHeaderClickable('results') ? () => setStep('results') : undefined}
                  >
                    {isGenerating && (
                      <div className="w-full mb-6">
                        <div className="text-xs text-left text-blue-600 min-h-[1.875rem]">
                          {(() => {
                            const logic = typingLogicRef.current;
                            let lineToDisplay: string | undefined;
                            let currentMessageContent: string | undefined;
                            let showCursor = false;
                            const pClassName = "m-0 p-0 leading-tight";
                            if (logic.isWaitingForNewLineDelay && logic.lineIdx > 0) {
                              const prevLineIdx = logic.lineIdx - 1;
                              currentMessageContent = DUMMY_MESSAGES[prevLineIdx];
                              lineToDisplay = typedLines[prevLineIdx] || currentMessageContent;
                              if (lineToDisplay && lineToDisplay.length === (currentMessageContent?.length || 0)) {
                                showCursor = true;
                              }
                            } else {
                              currentMessageContent = DUMMY_MESSAGES[logic.lineIdx];
                              lineToDisplay = typedLines[logic.lineIdx] || "";
                              if (logic.lineIdx < DUMMY_MESSAGES.length) {
                                if (lineToDisplay.length < (currentMessageContent?.length || 0)) {
                                    showCursor = true;
                                } else if (lineToDisplay === "" && currentMessageContent) {
                                    showCursor = true;
                                }
                              }
                            }
                            if (logic.lineIdx >= DUMMY_MESSAGES.length && logic.intervalId && DUMMY_MESSAGES.length > 0) {
                                const lastMessageIndex = DUMMY_MESSAGES.length - 1;
                                const lastTypedLine = typedLines[lastMessageIndex];
                                const lastDummyMessage = DUMMY_MESSAGES[lastMessageIndex];
                                if (lastTypedLine && lastDummyMessage && lastTypedLine.length === lastDummyMessage.length) {
                                    lineToDisplay = lastTypedLine;
                                    showCursor = true; 
                                }
                            }
                            if (lineToDisplay !== undefined) { 
                              return (
                                <p className={pClassName}>
                                  {lineToDisplay}
                                  {showCursor && <span className="blinking-cursor">_</span>}
                                </p>
                              );
                            } 
                            else if (isGenerating && logic.lineIdx === 0 && DUMMY_MESSAGES.length > 0 && typedLines.length > 0 && typedLines[0] === "") {
                               return (
                                <p className={pClassName}>
                                    <span className="blinking-cursor">_</span>
                                </p>
                               );
                            }
                            return <p className={pClassName}>&nbsp;</p>;
                          })()}
                        </div>
                        <div className="h-2 w-full bg-muted overflow-hidden rounded mt-1">
                          <div 
                            className="h-full bg-blue-700 transition-all duration-150 ease-in-out" 
                            style={{ width: `${generationProgress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                    {!isGenerating && generationError && currentWizardStep === 'results' && (
                      <div className="p-4 text-center">
                        <p
                          className="text-base text-red-500 mb-4"
                          dangerouslySetInnerHTML={{ __html: (typeof generationError === 'string' ? generationError : (generationError as any).message || 'An unexpected error occurred').replace(/<br\s*\/?b?>/gi, '<br />') }}
                        />
                        <div className="flex justify-center w-full mt-2">
                          <button type="button" onClick={handleGenerateImageClick} className={`px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 rounded-md shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 justify-center ${isGenerating ? 'opacity-60 cursor-not-allowed shadow-none text-muted-foreground border-muted-foreground' : ''}`} disabled={isGenerating}>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                            Retry Generation
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Conditional Block for Note Input (or Success Message) */}
                    {!isGenerating && !generationError && isResultsStepCompleted && currentWizardStep === 'results' && (
                      <>
                        {isNoteStepActive && currentDbId ? (
                          // If Note Step is Active: Show Card Front + Note Form
                          <div className="w-full p-1 md:p-2 space-y-4">
                            <div ref={cardDisplayControlsRef} className="w-full mx-auto mb-4">
                              {(currentDisplayOrientation === 'horizontal' && generatedHorizontalImageUrl) ? (
                                <img src={generatedHorizontalImageUrl} alt="Generated horizontal card (front)" className="w-full h-auto object-contain rounded-md aspect-[2/1]" />
                              ) : (currentDisplayOrientation === 'vertical' && generatedVerticalImageUrl) ? (
                                <img src={generatedVerticalImageUrl} alt="Generated vertical card (front)" className="w-full h-auto object-contain rounded-md aspect-[1/2]" />
                              ) : (
                                <div className="w-full aspect-[2/1] flex justify-center items-center bg-muted rounded-md">
                                  <p className="text-muted-foreground">Front image not available.</p>
                                </div>
                              )}
                            </div>
                            {/* New wrapper for textarea and char counter */}
                            <div> 
                              <textarea
                                value={noteText}
                                onChange={(e) => setNoteText(e.target.value)}
                                placeholder="Add your note here (optional, max 500 characters). Press Enter for new lines."
                                maxLength={500}
                                className="w-full h-24 p-3 bg-input border border-border rounded-md focus:ring-2 focus:ring-ring focus:border-ring placeholder-muted-foreground/70 text-foreground text-base resize"
                                aria-label="Note for the back of the card"
                              />
                              <div className="flex items-center justify-between mt-1"> {/* Added mt-1 for slight space, removed from parent's space-y effect */}
                                <p className="text-xs text-muted-foreground">
                                  {noteText.length}/500 characters
                                </p>
                              </div>
                            </div>
                            {noteSubmissionError && (
                              <p className="text-sm text-red-500 mt-2">{noteSubmissionError}</p>
                            )}
                            <div className="flex flex-col sm:flex-row gap-4 mt-4"> {/* Reverted container style */}
                              <button
                                onClick={() => handleNoteSubmission(noteText)}
                                disabled={isSubmittingNote || noteText.length > 500}
                                className="flex-1 px-6 py-3 font-semibold bg-black text-white border-2 border-[#374151] shadow-[4px_4px_0_0_#374151] hover:shadow-[2px_2px_0_0_#374151] active:shadow-[1px_1px_0_0_#374151] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none"
                              >
                                <PenSquare size={20} className="mr-2" /> {/* Reverted icon and text */}
                                Save The Note
                              </button>
                              <button
                                onClick={() => handleNoteSubmission()} 
                                disabled={isSubmittingNote}
                                className="px-6 py-3 font-semibold bg-background text-foreground border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none sm:w-auto"
                              >
                                <SkipForward size={20} className="mr-2" />
                                Skip Forever
                              </button>
                            </div>
                          </div>
                        ) : (
                          // If Note Step is NOT Active (but results are complete and no error)
                          <div className="p-2 text-center">
                            <p className="text-base">Your unique shadefreude card is ready.</p>
                            <p className="text-base">Now with its own story.</p>
                          </div>
                        )}
                      </>
                    )}

                    {/* Message for when color step is done, but results not yet generated */}
                    {!isGenerating && !isResultsStepCompleted && isColorStepCompleted && !generationError && currentWizardStep !== 'results' && (
                      <div className="p-4 text-center">
                        <p className="text-base text-muted-foreground">Ready to generate your card in Step 3.</p>
                      </div>
                    )}
                  </WizardStep>
                )}
              </section>
              {/* "+ Create New Card" button - MOVED BACK HERE, after wizard <section> */}
              {isNoteStepActive && isResultsStepCompleted && !isGenerating && (
                            <div className="mt-1 flex justify-center"> {/* mt-3 changed to mt-1 */}
              <button
                onClick={handleCreateNewCard}
                className="text-sm text-foreground hover:text-muted-foreground underline flex items-center justify-center gap-2 py-2"
                title="Create New Card"
              >
                + Create New Card
              </button>
            </div>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}