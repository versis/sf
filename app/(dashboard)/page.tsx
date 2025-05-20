'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import CardDisplay from '@/components/CardDisplay';
import { useState, useRef, useEffect } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'results';

const DUMMY_MESSAGES = [
  "Waking the muses of color for your special hue...",
  "My AI assistant is 'tinkering' with its poetic potential...",
  "Consulting the chromatic soul of your image...",
  "Now for its exclusive identity: assigning a unique serial number...",
  "It\'ll look like #000000XXX – each one is one-of-a-kind!...",
  "Then, it gets the special 'FE F' stamp...",
  "The 'FE' stands for 'First Edition'!",
  "And the 'F'? That means this creation is entirely 'Free' for you.",
  "The AI is distilling its essence, crafting a unique name and tale...",
  "It's taking a final look... (it\'s a bit of a perfectionist!)",
  "Polishing your unique color artifact...",
  "Get ready! Your personal shadefreude is about to debut."
];
const CHAR_TYPING_SPEED_MS = 30;
const NEW_LINE_DELAY_TICKS = Math.floor(2000 / CHAR_TYPING_SPEED_MS);

const EXAMPLE_CARDS = [
  { v: "/example-card-v-1.png", h: "/example-card-h-1.png" },
  { v: "/example-card-v-2.png", h: "/example-card-h-2.png" },
  { v: "/example-card-v-3.png", h: "/example-card-h-3.png" },
];
const SWIPE_THRESHOLD = 50; // Minimum pixels for a swipe to be registered

export default function HomePage() {
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

  // State for wizard completion
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  const [isResultsStepCompleted, setIsResultsStepCompleted] = useState(false);
  const [generatedExtendedId, setGeneratedExtendedId] = useState<string | null>(null);
  const [currentExampleCardIndex, setCurrentExampleCardIndex] = useState(0);
  const [touchStartX, setTouchStartX] = useState<number | null>(null);
  
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
    
    // Revoke URLs
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    console.log('Wizard reset.');
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
    
    const internalApiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY;
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

      const horizontalUrl = finalizeResult.horizontal_image_url;
      const verticalUrl = finalizeResult.vertical_image_url;
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
      title: 'Shadefreude Color Card',
      text: shareMessage,
      url: shareUrl, // Use the new sf.tinker.institute URL if available, otherwise blob URL
    };

    let copied = false;
    try {
      if (navigator.share) {
        await navigator.share(shareData);
        setShareFeedback('Shared successfully!'); // Or rely on system feedback
        // Optionally, still copy to clipboard as a fallback or primary action for some users
        // await navigator.clipboard.writeText(currentImageUrl);
        // copied = true;
      } else {
        // If navigator.share is not available, fall back to copying the URL and message
        await navigator.clipboard.writeText(shareMessage); // Copy the full message with URL
        copied = true;
        setShareFeedback('Share message with image link copied to clipboard!');
      }
    } catch (err) {
      console.error('Share/Copy failed:', err);
      // If navigator.share fails or is unavailable, ensure clipboard copy is attempted
      if (!copied) { 
        try {
          await navigator.clipboard.writeText(shareMessage); // Copy the full message with URL
          setShareFeedback('Share message with image link copied to clipboard!');
        } catch (copyErr) {
          console.error('Clipboard copy failed:', copyErr);
          setShareFeedback('Failed to copy link.');
        }
      } else if (!navigator.share) {
        // This case is already handled above where navigator.share is not available.
      } else {
        // If share API was present and failed, but copy succeeded (if we enabled copy above even on share success).
        // For now, the primary feedback for share failure is just logging the error.
        // If share fails, and we didn't try to copy, this is just a failed share.
        setShareFeedback('Sharing failed. Try copying the link.'); 
      }
    } finally {
      setTimeout(() => setShareFeedback(''), 3000);
      setCopyUrlFeedback(''); // Clear copy feedback if share is used
    }
  };

  const handleCopyGeneratedUrl = async () => {
    if (!generatedExtendedId) {
      setCopyUrlFeedback('Cannot copy URL: Card not yet fully generated.');
      setTimeout(() => setCopyUrlFeedback(''), 3000);
      return;
    }
    const slug = generatedExtendedId.replace(/\s+/g, '-').toLowerCase();
    const urlToCopy = `https://sf.tinker.institute/color/${slug}`;
    try {
      await navigator.clipboard.writeText(urlToCopy);
      setCopyUrlFeedback("Link to your shade's story, copied! Go on, spread the freude.");
    } catch (err) {
      console.error('Failed to copy generated URL:', err);
      setCopyUrlFeedback('Failed to copy URL.');
    }
    setTimeout(() => setCopyUrlFeedback(''), 3000);
    setShareFeedback(''); // Clear share feedback if copy is used
  };

  const handleNextExampleCard = () => {
    setCurrentExampleCardIndex((prevIndex) => (prevIndex + 1) % EXAMPLE_CARDS.length);
  };

  const handlePrevExampleCard = () => {
    setCurrentExampleCardIndex((prevIndex) => (prevIndex - 1 + EXAMPLE_CARDS.length) % EXAMPLE_CARDS.length);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
      <style jsx global>{`
        @keyframes shakeAnimation {
          0% { transform: translateX(0); }
          20% { transform: translateX(-4px); }
          40% { transform: translateX(4px); }
          60% { transform: translateX(-2px); }
          80% { transform: translateX(2px); }
          100% { transform: translateX(0); }
        }
        .shake-animation {
          animation: shakeAnimation 0.5s ease-in-out;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .blinking-cursor {
          display: inline-block;
          animation: blink 1s step-end infinite;
        }
        .scroll-target-with-offset {
          scroll-margin-top: 2rem; /* Adjust this value as needed */
        }
      `}</style>
      
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

        {/* Hero Section Text & Example Card */}
        <section className="w-full py-2 md:py-4">
          <div className="md:grid md:grid-cols-5 md:gap-8 lg:gap-12 items-start">
            {/* Left Column: Text - takes 2/5ths */}
            <div className="text-left mb-6 md:mb-0 md:col-span-2 pt-0">
              <h2 className="text-3xl md:text-4xl font-semibold mb-3">
                Your photo&apos;s hue,<br /> AI&apos;s poetic debut.
              </h2>
              <p className="text-md md:text-lg text-muted-foreground">
                Hi, I&apos;m Kuba, a data scientist who loves to tinker. I built shadefreude to blend a bit of AI magic with your everyday images. Pick a photo, choose a color that speaks to you, and my system will craft a unique name and a poetic little story for it. Think of this whole thing as an experiment, resulting in a unique and memorable artifact for your photo.
              </p>
            </div>

            {/* Right Column: Example Card with Navigation - takes 3/5ths */}
            <div className="flex flex-col md:items-start w-full md:col-span-3 relative md:-mt-3">
              {/* Image Container - Common for Mobile and Desktop Image Source */}
              <div 
                className={`relative w-full mb-2 cursor-grab active:cursor-grabbing 
                            ${isMobile ? 'max-w-lg aspect-[3/4] mx-auto' : 'max-w-xl aspect-video mx-auto'}`}
                onTouchStart={(e) => setTouchStartX(e.touches[0].clientX)}
                onTouchMove={(e) => { /* Visual feedback */ }}
                onTouchEnd={(e) => {
                  if (touchStartX === null) return;
                  const touchEndX = e.changedTouches[0].clientX;
                  const deltaX = touchEndX - touchStartX;
                  if (Math.abs(deltaX) > SWIPE_THRESHOLD) {
                    if (deltaX > 0) { handlePrevExampleCard(); }
                    else { handleNextExampleCard(); }
                  }
                  setTouchStartX(null);
                }}
              >
                <img 
                  src={isMobile ? EXAMPLE_CARDS[currentExampleCardIndex].v : EXAMPLE_CARDS[currentExampleCardIndex].h}
                  alt={`Example Shadefreude Card ${currentExampleCardIndex + 1}`}
                  className="w-full h-full rounded-lg object-contain"
                  draggable="false"
                />

                {/* Desktop Overlay/Side Buttons - Hidden on Mobile */}
                {!isMobile && (
                  <>
                    {currentExampleCardIndex > 0 && (
                      <button 
                        onClick={handlePrevExampleCard} 
                        className="absolute top-1/2 -left-4 md:-left-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                        aria-label="Previous example card"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
                      </button>
                    )}
                    {currentExampleCardIndex < EXAMPLE_CARDS.length - 1 && (
                      <button 
                        onClick={handleNextExampleCard} 
                        className="absolute top-1/2 -right-4 md:-right-8 transform -translate-y-1/2 text-muted-foreground hover:text-foreground z-10 transition-colors"
                        aria-label="Next example card"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
                      </button>
                    )}
                  </>
                )}
              </div>

              {/* Mobile Dot Indicators - Hidden on Desktop */}
              {isMobile && (
                <div className="flex justify-center items-center space-x-2 mt-3">
                    {EXAMPLE_CARDS.map((_, index) => (
                        <button
                        key={index}
                        onClick={() => setCurrentExampleCardIndex(index)}
                        className={`w-2.5 h-2.5 rounded-full transition-colors ${currentExampleCardIndex === index ? 'bg-foreground' : 'bg-muted hover:bg-muted-foreground/50'}`}
                        aria-label={`Go to example card ${index + 1}`}
                        />
                    ))}
                </div>
              )}
            </div>
          </div>
        </section>

        <div className={'grid grid-cols-1 md:grid-cols-1 gap-8 md:gap-12'}>
          <section className="w-full bg-card text-card-foreground border-2 border-foreground space-y-0 flex flex-col md:order-1">
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
              title="3: Select Your Signature Shade"
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
                    <div className="text-base text-left text-blue-600 mb-2 pl-2">
                      {typedLines.map((line, index) => {
                        const currentLogicLine = typingLogicRef.current.lineIdx;
                        const isWaitingForNextLine = typingLogicRef.current.isWaitingForNewLineDelay;
                        let showCursorOnThisLine = false;

                        if (currentLogicLine < DUMMY_MESSAGES.length) { 
                            if (index === currentLogicLine && !isWaitingForNextLine) {
                                showCursorOnThisLine = true;
                            } else if (index === currentLogicLine - 1 && isWaitingForNextLine) {
                                showCursorOnThisLine = true;
                            }
                        } else if (currentLogicLine === DUMMY_MESSAGES.length && index === DUMMY_MESSAGES.length - 1) {
                            // Show cursor on the very last character of the last line if interval is still active
                            if (typedLines[index] && DUMMY_MESSAGES[index] && typedLines[index].length === DUMMY_MESSAGES[index].length && typingLogicRef.current.intervalId) {
                                showCursorOnThisLine = true;
                            }
                        }

                        return (
                          <p key={index} className="whitespace-pre-wrap m-0 p-0 leading-tight">
                            {line}
                            {showCursorOnThisLine && (<span className="blinking-cursor">_</span>)}
                          </p>
                        );
                      })}
                      {typedLines.length === 0 && isGenerating && typingLogicRef.current.lineIdx === 0 && DUMMY_MESSAGES.length > 0 && (
                        <p className="whitespace-pre-wrap m-0 p-0 leading-tight"><span className="blinking-cursor">_</span></p>
                      )}
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
                      dangerouslySetInnerHTML={{
                        __html: (typeof generationError === 'string' ? 
                                 generationError : 
                                 (generationError as any).message || 'An unexpected error occurred'
                                ).replace(/<br\s*\/?b?>/gi, '<br />')
                      }}
                    />
                    <div className="flex justify-center w-full mt-2">
                      <button
                        type="button"
                        onClick={handleGenerateImageClick}
                        className={`px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 rounded-md shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 justify-center 
                          ${isGenerating ? 'opacity-60 cursor-not-allowed shadow-none text-muted-foreground border-muted-foreground' : ''}`}
                        disabled={isGenerating}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="23 4 23 10 17 10"></polyline>
                          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                        </svg>
                        Retry Generation
                      </button>
                    </div>
                  </div>
                )}
                {!isGenerating && isResultsStepCompleted && !generationError && currentWizardStep === 'results' && (
                  <div className="p-2 text-center">
                    <p className="text-base">Your unique hue, now with its own story.</p>
                  </div>
                )}
                 {!isGenerating && !isResultsStepCompleted && isColorStepCompleted && !generationError && currentWizardStep !== 'results' && (
                  <div className="p-4 text-center">
                    <p className="text-base text-muted-foreground">Ready to generate your card in Step 3.</p>
                  </div>
                )}
              </WizardStep>
            )}
          </section>

          {/* New Section for Card Display - Outside/Below Wizard */}
          <CardDisplay
            isVisible={!!(isResultsStepCompleted && !isGenerating && (generatedHorizontalImageUrl || generatedVerticalImageUrl))}
            generatedHorizontalImageUrl={generatedHorizontalImageUrl}
            generatedVerticalImageUrl={generatedVerticalImageUrl}
            currentDisplayOrientation={currentDisplayOrientation}
            setCurrentDisplayOrientation={setCurrentDisplayOrientation}
            handleShare={handleShare}
            handleCopyGeneratedUrl={handleCopyGeneratedUrl}
            handleDownloadImage={handleDownloadImage}
            resetWizard={resetWizard}
            isGenerating={isGenerating}
            generatedExtendedId={generatedExtendedId}
            cardDisplayControlsRef={cardDisplayControlsRef} // Pass the existing ref
            shareFeedback={shareFeedback}
            copyUrlFeedback={copyUrlFeedback}
          />
        </div>
      </div>
    </main>
  );
}