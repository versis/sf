'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'results';

const DUMMY_MESSAGES = [
  "Initializing generation sequence...",
  "Querying neural network for inspiration...",
  "Synthesizing color harmonies...",
  "Finalizing your unique design...",
  "Still waiting for AI. As usuall..."
];
const CHAR_TYPING_SPEED_MS = 30;
const NEW_LINE_DELAY_TICKS = Math.floor(2000 / CHAR_TYPING_SPEED_MS);

export default function HomePage() {
  const [uploadStepPreviewUrl, setUploadStepPreviewUrl] = useState<string | null>(null);
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [generatedVerticalImageUrl, setGeneratedVerticalImageUrl] = useState<string | null>(null);
  const [generatedHorizontalImageUrl, setGeneratedHorizontalImageUrl] = useState<string | null>(null);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorNameInput, setColorNameInput] = useState<string>('EXAMPLE COLOR NAME');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const [userHasInteractedWithColor, setUserHasInteractedWithColor] = useState(false);
  const [showColorInstructionHighlight, setShowColorInstructionHighlight] = useState(false);
  const [colorInstructionKey, setColorInstructionKey] = useState(0);
  const [isMobile, setIsMobile] = useState<boolean>(false);

  // State for wizard completion
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  const [isResultsStepCompleted, setIsResultsStepCompleted] = useState(false);
  
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
    setCurrentDisplayOrientation('horizontal');
    setIsGenerating(false);
    setGenerationError(null);
    setColorNameInput('EXAMPLE COLOR NAME');
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
      const extendedId = initiateResult.extended_id;
      console.log(`Frontend: Initiation successful. DB ID: ${dbId}, Extended ID: ${extendedId}`);
      // setGenerationProgress(30); // REMOVE discrete progress update

      // Convert base64 Data URL to Blob for multipart/form-data upload
      const fetchRes = await fetch(croppedImageDataUrl!);
      const blob = await fetchRes.blob();
      const imageFile = new File([blob], selectedFileName || 'user_image.png', { type: blob.type });

      // STEP 2: Finalize Card Generation
      console.log(`Frontend: Finalizing card generation for DB ID: ${dbId} with name: ${colorNameInput}`);
      const formData = new FormData();
      formData.append('user_image', imageFile);
      formData.append('card_name', colorNameInput);
      // Add other optional fields if needed, e.g., user_prompt, ai_generated_details
      // formData.append('user_prompt', 'some prompt'); 

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
      setCurrentWizardStep('results'); 
      setIsResultsStepCompleted(true);
      // console.log('Frontend: State updated for results step. currentWizardStep:', 'results'); // DEBUG REMOVED
      
      // Set the display orientation based on availability and preference
      if (isMobile && verticalUrl) {
        setCurrentDisplayOrientation('vertical');
      } else if (horizontalUrl) {
        setCurrentDisplayOrientation('horizontal');
      } else if (verticalUrl) {
        setCurrentDisplayOrientation('vertical');
      }

      // setGenerationProgress(100); // REMOVE discrete progress update, handled by interval or finally block
      clearInterval(progressInterval); // Ensure interval is cleared on successful completion
      setGenerationProgress(100); // Explicitly set to 100 on success

    } catch (error) {
      console.error('Frontend: Error during image generation process:', error); // KEEP this generic error log
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred.');
      setGeneratedHorizontalImageUrl(null); 
      setGeneratedVerticalImageUrl(null);
      setIsColorStepCompleted(false); 
      setCurrentWizardStep('color'); 
      if (dbId) {
        console.warn(`Generation failed after initiating with DB ID: ${dbId}. Status on server might be pending/failed.`);
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

        <div className={'grid grid-cols-1 md:grid-cols-1 gap-8 md:gap-12'}>
          <section className="w-full bg-card text-card-foreground border-2 border-foreground space-y-0 flex flex-col md:order-1">
            <WizardStep 
              title="Pick a nice photo you like"
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
              title="We need to cut a square"
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
              title="Choose your color"
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
                    {isGenerating ? 'Generating Card...' : 'I want this color - show me the card'}
                  </button>
                </div>
              </WizardStep>
            )}

            {(isCropStepCompleted && (currentWizardStep === 'results' || isGenerating)) && (
              <WizardStep
                title="Your shadefreude color card"
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

                {!isGenerating && (generatedHorizontalImageUrl || generatedVerticalImageUrl) && (
                  <div className="space-y-4 flex flex-col items-center">
                    <div className="flex justify-center gap-6 mb-4">
                      <button 
                        onClick={() => setCurrentDisplayOrientation('horizontal')}
                        className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'horizontal' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
                        title="Display Horizontal Card"
                        disabled={isGenerating || !generatedHorizontalImageUrl}
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2" ry="2" /></svg>
                        <span className="text-xs mt-1">Horizontal</span>
                      </button>
                <button 
                  onClick={() => setCurrentDisplayOrientation('vertical')}
                        className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'vertical' ? 'border-blue-700 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'} flex flex-col items-center transition-all duration-200`}
                        title="Display Vertical Card"
                        disabled={isGenerating || !generatedVerticalImageUrl}
                >
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="3" width="14" height="18" rx="2" ry="2" /></svg>
                  <span className="text-xs mt-1">Vertical</span>
                </button>
              </div>

                    <div className="flex justify-center w-full">
                      {(currentDisplayOrientation === 'horizontal' && generatedHorizontalImageUrl) ? (
                        <img src={generatedHorizontalImageUrl} alt="Generated horizontal card" className={`max-w-full rounded-md md:max-w-2xl h-auto`} />
                      ) : (currentDisplayOrientation === 'vertical' && generatedVerticalImageUrl) ? (
                        <img src={generatedVerticalImageUrl} alt="Generated vertical card" className={`max-w-full rounded-md md:max-w-sm max-h-[80vh] h-auto`} />
                      ) : (
                        <p className="text-muted-foreground">Select an orientation to view.</p>
              )}
            </div>
            
                    <div className="flex justify-center gap-4 mt-4">
                <button
                    onClick={() => handleDownloadImage(currentDisplayOrientation)}
                        disabled={isGenerating || (currentDisplayOrientation === 'horizontal' ? !generatedHorizontalImageUrl : !generatedVerticalImageUrl)}
                        className="px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Download
                      </button>
                    </div>
                    
                    <button
                      onClick={resetWizard}
                      className="mt-6 px-4 py-2 text-sm text-muted-foreground hover:text-foreground underline"
                    >
                      Create New Card
                </button>
                  </div>
                )}
              </WizardStep>
              )}
          </section>
        </div>
      </div>
    </main>
  );
}