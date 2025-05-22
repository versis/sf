'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';
import { copyTextToClipboard } from '@/lib/clipboardUtils';
import { shareOrCopy } from '@/lib/shareUtils';
import { COPY_SUCCESS_MESSAGE } from '@/lib/constants';
import { useRouter } from 'next/navigation';
import { Save, SkipForward, PenSquare, ChevronDown, ChevronUp, Palette, UploadCloud, Wand2, Eye, RotateCcw,
  Copy, Check, Share2, Download, AlertTriangle, MoreHorizontal, X, ExternalLink,
  Image as ImageIcon, Trash2, Info, SquareArrowOutUpRight, Undo2, BookOpenText } from 'lucide-react';

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

// User-provided IDs (ensure these are correct and exist in your DB)
const HERO_EXAMPLE_CARD_EXTENDED_IDS = [
  "000000063 FE F",
  "000000064 FE F",
  "000000065 FE F",
  // Add more valid extended_ids from your database here
];
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
  const [isHeroVisible, setIsHeroVisible] = useState(true);

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
  const [animationClass, setAnimationClass] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [displayedImageSrc, setDisplayedImageSrc] = useState<string>('');
  
  const [currentDbId, setCurrentDbId] = useState<number | null>(null);
  
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
  const [fetchedHeroCards, setFetchedHeroCards] = useState<Array<{ id: string; v: string | null; h: string | null }>>([]);
  
  // New states for note feature
  const [noteText, setNoteText] = useState<string>("");
  const [isNoteStepActive, setIsNoteStepActive] = useState<boolean>(false);
  const [isSubmittingNote, setIsSubmittingNote] = useState<boolean>(false);
  const [noteSubmissionError, setNoteSubmissionError] = useState<string | null>(null);
  
  const mainContainerRef = useRef<HTMLDivElement>(null); // Ref for the main content container
  
  const internalApiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY;

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
    const fetchAllHeroCards = async () => {
      if (HERO_EXAMPLE_CARD_EXTENDED_IDS.length === 0) {
        console.log("[Hero Data] No hero card IDs provided.");
        setHeroCardsLoading(false);
        setFetchedHeroCards([]);
        return;
      }
      console.log("[Hero Data] Starting to fetch hero cards for IDs:", HERO_EXAMPLE_CARD_EXTENDED_IDS);
      setHeroCardsLoading(true);
      
      const cardDataPromises = HERO_EXAMPLE_CARD_EXTENDED_IDS.map(async (extendedId) => {
        try {
          const encodedExtendedId = encodeURIComponent(extendedId);
          const response = await fetch(`/api/retrieve-card-by-extended-id/${encodedExtendedId}`);
          if (!response.ok) {
            console.error(`[Hero Data] Failed to fetch hero card ${extendedId} (encoded: ${encodedExtendedId}): ${response.status} ${response.statusText}`);
            return null; 
          }
          const data = await response.json();
          return {
            id: extendedId, // Store original ID for reference if needed
            v: data.frontVerticalImageUrl || null,
            h: data.frontHorizontalImageUrl || null,
          };
        } catch (error) {
          console.error(`[Hero Data] Error fetching hero card ${extendedId}:`, error);
          return null;
        }
      });

      const results = await Promise.all(cardDataPromises);
      console.log("[Hero Data] Raw fetched results for all hero card IDs:", JSON.stringify(results, null, 2));
      
      const filteredResults = results.filter(card => card !== null && (card.v || card.h)) as Array<{ id: string; v: string | null; h: string | null }>;
      console.log("[Hero Data] Filtered results (non-null with at least one image URL) being set to state:", JSON.stringify(filteredResults, null, 2));
      
      setFetchedHeroCards(filteredResults);
      setHeroCardsLoading(false);
    };

    fetchAllHeroCards();
  }, []); // Empty dependency array: Runs once on mount

  // Initialize displayedImageSrc based on initial currentExampleCardIndex, isMobile, and fetchedHeroCards
  useEffect(() => {
    if (!heroCardsLoading && fetchedHeroCards.length > 0) {
      const card = fetchedHeroCards[currentExampleCardIndex];
      if (card) {
        const initialImage = isMobile ? card.v : card.h;
        if (initialImage) {
          setDisplayedImageSrc(initialImage);
          console.log("[Hero Init] Initial displayedImageSrc set to:", initialImage);
        } else {
          // Fallback if preferred orientation is missing for the first card
          const fallbackImage = isMobile ? card.h : card.v;
          if (fallbackImage) {
            setDisplayedImageSrc(fallbackImage);
            console.log("[Hero Init] Initial displayedImageSrc (fallback) set to:", fallbackImage);
          } else {
            console.warn(`[Hero Init] Card at index ${currentExampleCardIndex} has no image URLs.`);
            // setDisplayedImageSrc('/placeholder-hero.png'); // Optional placeholder
          }
        }
      } else {
        console.warn(`[Hero Init] No card data found at currentExampleCardIndex: ${currentExampleCardIndex} after loading.`);
      }
    } else if (!heroCardsLoading && fetchedHeroCards.length === 0 && HERO_EXAMPLE_CARD_EXTENDED_IDS.length > 0) {
        console.warn("[Hero Init] Hero cards were fetched, but the resulting array is empty or all items filtered out.");
        // setDisplayedImageSrc('/placeholder-hero.png'); // Optional placeholder
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

    setIsHeroVisible(false);

    // Revoke URLs
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    console.log('Wizard reset.');

    // Reset animation states
    setSwipeDeltaX(0);
    setAnimationClass('');
    setIsAnimating(false);
  };

  const handleImageSelectedForUpload = (file: File) => {
    // Reset relevant parts of the wizard when a new image is selected
    resetWizard(); // Call full reset and then set new state
    setCurrentWizardStep('upload'); // Will be set by resetWizard, but to be explicit

    console.log(`STEP 1.1: Original file selected - Name: ${file.name}, Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`);
    setSelectedFileName(file.name);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      setUploadStepPreviewUrl(dataUrl);
      setIsUploadStepCompleted(true);
      setCurrentWizardStep('crop'); // Move to next step
    };
    reader.onerror = () => {
      console.error('Error reading file for preview.');
      setGenerationError('Error reading file for preview.');
      resetWizard(); // Reset if file reading fails
    };
    reader.readAsDataURL(file);
  };

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

      // Preload the initially displayed image and scroll after it loads
      if (initialDisplayUrl) {
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
      } else {
        // If no specific image to preload (should not happen if URLs are present),
        // scroll immediately (or with a small delay as a fallback)
        setTimeout(() => {
            cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        },100);
      }

      // setGenerationProgress(100); // REMOVE discrete progress update, handled by interval or finally block
      clearInterval(progressInterval); // Ensure interval is cleared on successful completion
      setGenerationProgress(100); // Explicitly set to 100 on success
      
      // Activate the note input step instead of immediately redirecting
      setIsNoteStepActive(true);
      // Scroll to the note input section (we might need a ref for this later)
      // For now, the card display controls ref might be close enough or we adjust scroll target later.
      cardDisplayControlsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }); 

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
    console.log(`[Hero] Animation ended: ${animationClass}`);
    
    // Only handle slide-out animations ending here
    if (animationClass.includes('slide-out')) {
      // Animation end is handled via setTimeout in triggerImageChangeAnimation
      console.log(`[Hero] Slide-out animation completed`);
    } else if (animationClass === 'snap-back-animation') {
      // Handle snap-back for swipe that didn't reach threshold
      console.log(`[Hero] Snap-back animation completed`);
      setAnimationClass('');
      setIsAnimating(false);
      setSwipeDeltaX(0);
    }
  };

  // For the CSS transitions (slide-from-left/right), we need to handle transitionend events
  const handleTransitionEnd = () => {
    if (animationClass === 'slide-from-left' || animationClass === 'slide-from-right') {
      console.log(`[Hero] Slide-in transition completed`);
      setAnimationClass(''); // Remove transition class after complete
      setIsAnimating(false);
      setSwipeDeltaX(0);
    }
  };

  const triggerImageChangeAnimation = (direction: 'next' | 'prev', targetIndex?: number) => {
    // Don't start a new animation if one is already in progress
    if (isAnimating) return;
    
    setIsAnimating(true);
    console.log(`[Hero] Starting ${direction} animation`);

    // Calculate the target index
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

    console.log(`[Hero] Navigating from card ${currentExampleCardIndex} to ${newIndex}`);

    // Get the card data for the target index
    const card = fetchedHeroCards[newIndex];
    if (!card) {
      console.error(`[Hero] No card data for index ${newIndex}`);
      setIsAnimating(false);
      return;
    }

    // Select the appropriate image based on device
    const imageUrl = isMobile 
      ? card.v || card.h // Prefer vertical on mobile, fallback to horizontal
      : card.h || card.v; // Prefer horizontal on desktop, fallback to vertical

    if (!imageUrl) {
      console.error(`[Hero] No image available for card at index ${newIndex}`);
      setIsAnimating(false);
      return;
    }

    // Set the slide-out animation class
    setAnimationClass(direction === 'next' ? 'slide-out-left-animation' : 'slide-out-right-animation');

    // Preload the image
    const img = new Image();
    img.onload = () => {
      console.log(`[Hero] Next image loaded: ${imageUrl}`);
      
      // We'll use a completely different approach with CSS transitions instead of animations
    // This gives us more control over the timing and prevents double-loading appearance
    
    // First, wait for the slide-out animation to complete
    setTimeout(() => {
      // Prepare for the immediate transition on next render
      if (direction === 'next') {
        // No animation class - just update the image, which will be initially invisible
        setAnimationClass('prepare-from-right');
        setDisplayedImageSrc(imageUrl);
        setCurrentExampleCardIndex(newIndex);
        
        // Force browser to process the above changes before starting animation
        setTimeout(() => {
          // Now trigger the slide-in with CSS transition
          setAnimationClass('slide-from-right');
        }, 20);
      } else {
        // Same flow for previous direction
        setAnimationClass('prepare-from-left');
        setDisplayedImageSrc(imageUrl);
        setCurrentExampleCardIndex(newIndex);
        
        setTimeout(() => {
          setAnimationClass('slide-from-left');
        }, 20);
      }
    }, 300); // Match this to the slide-out animation duration in CSS
    };
    
    img.onerror = () => {
      console.error(`[Hero] Failed to load image: ${imageUrl}`);
      setAnimationClass('');
      setIsAnimating(false);
    };
    
    img.src = imageUrl;
  };

  const handleNextExampleCard = () => {
    triggerImageChangeAnimation('next');
  };

  const handlePrevExampleCard = () => {
    triggerImageChangeAnimation('prev');
  };

  const handleDotClick = (index: number) => {
    if (isAnimating || index === currentExampleCardIndex) return;
    const direction = index > currentExampleCardIndex ? 'next' : 'prev'; // Simplistic, assumes not wrapping around for direction
                                                                    // More robust: check if it's shorter to go next or prev for wrapping
    // A more robust way to determine direction for dots when wrapping is needed:
    // const numCards = EXAMPLE_CARDS.length;
    // const diff = index - currentExampleCardIndex;
    // let determinedDirection: 'next' | 'prev' = 'next';
    // if (diff < 0) { // Target is "before" current
    //    determinedDirection = (Math.abs(diff) < numCards / 2) ? 'prev' : 'next'; // Go prev if shorter, else wrap next
    // } else { // Target is "after" current
    //    determinedDirection = (diff < numCards / 2) ? 'next' : 'prev'; // Go next if shorter, else wrap prev
    // }
    // For simplicity, let's stick to the basic direction for now as clicks are usually direct.
    triggerImageChangeAnimation(direction, index);
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

  return (
    <main ref={mainContainerRef} tabIndex={-1} className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground focus:outline-none">
      <div className="w-full max-w-6xl space-y-6" ref={resultRef}>
        <header className="py-6 border-b-2 border-foreground">
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

        {/* Control to Show Hero Section when it's hidden */}
        {!isHeroVisible && (
          <div className="w-full flex items-center justify-start mb-3 md:mb-4 pt-2 md:pt-4">
            <button
              onClick={() => setIsHeroVisible(true)}
              className="flex items-center text-left text-sm font-medium text-muted-foreground hover:text-foreground hover:underline focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md transition-colors p-1 gap-1" // Adjusted text size, added gap
              aria-label="Remind me what this page is about"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
              <span>Remind me what shadefreude is about</span>
            </button>
          </div>
        )}

        {/* Hero Section Text & Example Card */}
        {isHeroVisible && (
          <section className="w-full py-2 md:py-4">
            <div className="md:grid md:grid-cols-5 md:gap-8 lg:gap-12 items-start">
              {/* Left Column: Text - takes 2/5ths */}
              <div className="text-left mb-6 md:mb-0 md:col-span-2 pt-0">
                <h2 className="text-2xl md:text-3xl font-semibold mb-3">
                  Your Everyday Moments, <br />AI&apos;s Extraordinary Postcards
                </h2>
                <p className="text-md md:text-lg text-muted-foreground">
                  Upload a photo from your everyday life, pick a color you love, and watch as AI transforms it into a poetic digital postcard. The shade you choose earns its own evocative title and mini-story, while you add a personal note on the back—turning an ordinary snap into a share-worthy memento.
                </p>
              </div>

              {/* Right Column: Example Card with Navigation - takes 3/5ths */}
              <div className="flex flex-col md:items-start w-full md:col-span-3 relative md:-mt-3">
                <div
                  className={'relative w-full mb-2 cursor-grab active:cursor-grabbing overflow-hidden example-card-image-container'}
                  onTouchStart={(e) => {
                    if (isAnimating) return;
                    setTouchStartX(e.touches[0].clientX);
                    setAnimationClass('');
                    setSwipeDeltaX(0); // Reset delta for direct interaction on image
                  }}
                  onTouchMove={(e) => {
                    if (touchStartX === null || isAnimating) return;
                    const currentX = e.touches[0].clientX;
                    const delta = currentX - touchStartX;
                    setSwipeDeltaX(delta);
                  }}
                  onTouchEnd={(e) => {
                    if (touchStartX === null || isAnimating) return;
                    if (Math.abs(swipeDeltaX) > SWIPE_THRESHOLD) {
                      setIsAnimating(true);
                      if (swipeDeltaX < 0) {
                        triggerImageChangeAnimation('next');
                      } else {
                        triggerImageChangeAnimation('prev');
                      }
                    } else {
                      // Snap back if swipe was not strong enough
                      setAnimationClass('snap-back-animation');
                      // swipeDeltaX will be reset by handleAnimationEnd after snap-back
                    }
                    setTouchStartX(null);
                  }}
                >
                  {heroCardsLoading ? (
                    <div className="w-full h-auto max-h-[80vh] md:max-h-none rounded-lg bg-muted flex items-center justify-center aspect-[4/3] mx-auto">
                      <p className="text-muted-foreground">Loading examples...</p>
                      {/* Optional: Add a spinner SVG icon here */}
                    </div>
                  ) : fetchedHeroCards.length > 0 && displayedImageSrc ? (
                    <img
                      key={displayedImageSrc} // Add key for re-rendering on src change
                      src={displayedImageSrc}
                      alt={`Example shadefreude Card ${currentExampleCardIndex + 1} - ${fetchedHeroCards[currentExampleCardIndex]?.id}`}
                      className={`w-full h-auto max-h-[80vh] md:max-h-none rounded-lg object-contain example-card-image ${animationClass} ${swipeDeltaX !== 0 && !animationClass ? '' : 'transitioning'} mx-auto`}
                      style={{ transform: (swipeDeltaX !== 0 && !animationClass) ? `translateX(${swipeDeltaX}px)` : undefined }}
                      draggable="false"
                      onAnimationEnd={handleAnimationEnd}
                      onTransitionEnd={handleTransitionEnd}
                      onError={(e) => { 
                          console.error("[Hero Image Error] Failed to load displayedImageSrc:", displayedImageSrc, e);
                          // Optionally set to a placeholder if an image fails to load, e.g.:
                          // setDisplayedImageSrc('/placeholder-error.png'); 
                      }}
                    />
                  ) : (
                    <div className="w-full h-auto max-h-[80vh] md:max-h-none rounded-lg bg-muted flex items-center justify-center aspect-[4/3] mx-auto">
                      <p className="text-muted-foreground">No example images available.</p>
                    </div>
                  )}
                </div>

                {/* Desktop Overlay/Side Buttons - Hidden on Mobile */}
                {!isMobile && fetchedHeroCards.length > 1 && (
                  <>
                    {currentExampleCardIndex > 0 && (
                      <button
                        onClick={handlePrevExampleCard}
                        className="absolute top-1/2 -left-4 md:-left-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                        aria-label="Previous example card"
                        disabled={isAnimating}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                      </button>
                    )}
                    {currentExampleCardIndex < fetchedHeroCards.length - 1 && (
                      <button
                        onClick={handleNextExampleCard}
                        className="absolute top-1/2 -right-4 md:-right-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                        aria-label="Next example card"
                        disabled={isAnimating}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                      </button>
                    )}
                  </>
                )}

                {/* Mobile Dot Indicators - Hidden on Desktop */}
                {isMobile && fetchedHeroCards.length > 1 && (
                  <div className="flex justify-center items-center space-x-2 mt-3">
                      {fetchedHeroCards.map((card, index) => (
                          <button
                          key={card.id || index} // Use card.id if available, otherwise index
                          onClick={() => handleDotClick(index)}
                          className={`w-2.5 h-2.5 rounded-full transition-colors ${currentExampleCardIndex === index ? 'bg-foreground' : 'bg-gray-300 hover:bg-gray-400'}`}
                          aria-label={`Go to example card ${index + 1}`}
                          />
                      ))}
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        <hr className="w-full border-t-2 border-foreground my-6" />

        {/* Inserted Title and HR */}
        <div className="w-full flex flex-col items-start my-4">
          <h2 className="text-2xl md:text-3xl font-bold text-left mt-2">Create Your Card</h2>
        </div>

        <div className={'grid grid-cols-1 md:grid-cols-1 gap-8 md:gap-4'}>
          <section className="w-full bg-card text-card-foreground border-2 border-foreground space-y-0 flex flex-col">
            <WizardStep 
              title="1: Begin with an Image"
              stepNumber={1} 
              isActive={currentWizardStep === 'upload'} 
              isCompleted={isUploadStepCompleted}
              onHeaderClick={isStepHeaderClickable('upload') ? () => setStep('upload') : undefined}
            >
              <ImageUpload 
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
              title="2: Frame Your Focus"
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
                    key={`cropper-${uploadStepPreviewUrl}`}
                  />
              )}
            </WizardStep>
            )}

            {isCropStepCompleted && (
            <WizardStep 
              title="3: Pick Your Signature Shade"
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
                title="4: Your Shade Takes Form..."
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
                            <img src={generatedVerticalImageUrl} alt="Generated vertical card (front)" className="w-full h-auto object-contain rounded-md aspect-[1/2] max-h-[70vh]" />
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
                            placeholder="Add your note here (optional, max 500 characters). It will be placed on the back of the card..."
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
                            className="flex-1 px-6 py-3 font-semibold bg-black text-white border-2 border-gray-700 shadow-[4px_4px_0_0_#4A5568] hover:shadow-[2px_2px_0_0_#4A5568] active:shadow-[1px_1px_0_0_#4A5568] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center justify-center disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none"
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
                onClick={resetWizard}
                className="text-sm text-foreground hover:text-muted-foreground underline flex items-center justify-center gap-2 py-2"
                title="Create New Card"
              >
                + Create New Card
              </button>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}