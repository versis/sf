'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'results';

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
  
  // Store the db_id and extended_id from the initiate step
  const [generationDbId, setGenerationDbId] = useState<number | null>(null);
  const [generationExtendedId, setGenerationExtendedId] = useState<string | null>(null);

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
    setGenerationDbId(null); // Reset DB ID
    setGenerationExtendedId(null); // Reset extended ID

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
    setGenerationProgress(0);
    
    // Immediately move to step 4 (results) to show progress bar there
    setCurrentWizardStep('results');
    
    // Start the progress bar: 30-second duration, smooth constant increment
    const totalProgressDuration = 30000; // 30 seconds in milliseconds
    const updatesPerSecond = 10; // Update 10 times per second for smoothness
    const progressIntervalTime = 1000 / updatesPerSecond; // 100ms interval
    const totalUpdates = totalProgressDuration / progressIntervalTime; // 30s * 10fps = 300 updates
    const progressIncrement = 100 / totalUpdates; // Increment to reach 100% over totalUpdates

    let currentProgressValue = 0;
    setGenerationProgress(0);

    const progressInterval = setInterval(() => {
      currentProgressValue += progressIncrement;
      const newProgress = Math.min(100, currentProgressValue); // Cap at 100
      setGenerationProgress(newProgress);

      if (newProgress >= 100) {
        clearInterval(progressInterval);
      }
    }, progressIntervalTime);
    
    // Clear previous images before new generation
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    
    const apiKey = process.env.NEXT_PUBLIC_INTERNAL_API_KEY;
    const commonHeaders: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (apiKey) {
      commonHeaders['X-Internal-API-Key'] = apiKey;
    } else {
      console.warn('X-Internal-API-Key (NEXT_PUBLIC_INTERNAL_API_KEY) is not set in frontend environment. API calls may fail.');
    }

    try {
      // Step 1: Initiate card generation
      console.log("Calling /api/initiate-card-generation with color:", selectedHexColor);
      const initiateResponse = await fetch('/api/initiate-card-generation', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify({
          hex_color: selectedHexColor,
        }),
      });

      const initiateResult = await initiateResponse.json();
      if (!initiateResponse.ok) {
        throw new Error(initiateResult.detail || `Initiation failed with status: ${initiateResponse.status}`);
      }

      const { db_id, extended_id } = initiateResult;
      if (!db_id || !extended_id) {
        throw new Error('Initiation did not return valid db_id or extended_id.');
      }
      setGenerationDbId(db_id);
      setGenerationExtendedId(extended_id);
      console.log(`Initiation successful. DB ID: ${db_id}, Extended ID: ${extended_id}`);

      // Step 2: Finalize card generation
      // The extended_id is now available. The backend's generate_card_image_bytes 
      // will use this (passed as card_details.cardId) to render it on the image.
      // The croppedImageDataUrl is the base image for this process.
      console.log(`Calling /api/finalize-card-generation for DB ID: ${db_id}`);
      const finalizeResponse = await fetch('/api/finalize-card-generation', {
        method: 'POST',
        headers: commonHeaders,
        body: JSON.stringify({
          db_id: db_id,
          cropped_image_data_url: croppedImageDataUrl, // This is the base64 data URL
          hex_color: selectedHexColor, 
        }),
      });

      const finalizeResult = await finalizeResponse.json();

      if (!finalizeResponse.ok) {
        throw new Error(finalizeResult.detail || `Finalization failed with status: ${finalizeResponse.status}`);
      }

      if (finalizeResult.error) { // Check for application-level error in finalize result
        throw new Error(finalizeResult.error);
      }

      if (!finalizeResult.image_url) {
        throw new Error('Finalization did not return an image URL.');
      }

      // For now, let's assume it's a horizontal image, or adjust based on actual API response if it specifies orientation
      // setGeneratedHorizontalImageUrl(finalizeResult.image_url); 
      // If your backend's finalize can produce both, you'd get two URLs and set both
      // setGeneratedVerticalImageUrl(finalizeResult.vertical_image_url); 

      if (finalizeResult.horizontal_image_url) {
        setGeneratedHorizontalImageUrl(finalizeResult.horizontal_image_url);
      }
      if (finalizeResult.vertical_image_url) {
        setGeneratedVerticalImageUrl(finalizeResult.vertical_image_url);
      }

      if (finalizeResult.ai_details_used && finalizeResult.ai_details_used.colorName) {
        setColorNameInput(finalizeResult.ai_details_used.colorName);
      }

      // Successfully finalized
      setIsColorStepCompleted(true);
      setCurrentWizardStep('results');
      setIsResultsStepCompleted(true);

      // Determine display orientation based on what was generated
      if (isMobile && finalizeResult.vertical_image_url) {
         setCurrentDisplayOrientation('vertical');
      } else if (finalizeResult.horizontal_image_url) { 
         setCurrentDisplayOrientation('horizontal');
      } else if (finalizeResult.vertical_image_url) { // Fallback if horizontal wasn't generated but vertical was
         setCurrentDisplayOrientation('vertical');
      } 

      clearInterval(progressInterval); // Stop interval if API finishes early
      setGenerationProgress(100);

    } catch (error) {
      console.error('Error during image generation:', error);
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred.');
      // Clear any potentially set image URLs if error occurs mid-process
      setGeneratedHorizontalImageUrl(null); 
      setGeneratedVerticalImageUrl(null);
      setIsColorStepCompleted(false); // Generation failed, so color step not truly done for advancing
      if (generationProgress < 100) { // Ensure interval is cleared if not already done
          clearInterval(progressInterval);
          setGenerationProgress(0); // Reset progress on error
      }
    } finally {
      setIsGenerating(false);
      // Ensure progress is 100 if it wasn't already (e.g. error or early finish)
      // but don't clear interval here if it's already cleared above
      if (generationProgress < 100) {
         clearInterval(progressInterval);
         setGenerationProgress(100); 
      }
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
    if (stepName === 'results' && (isResultsStepCompleted || (currentWizardStep === 'results' && isColorStepCompleted))) return true;
    return false;
  };

  const handleDownloadImage = (orientation: 'vertical' | 'horizontal' = 'vertical') => {
    const imageUrl = orientation === 'vertical' ? generatedVerticalImageUrl : generatedHorizontalImageUrl;
    if (!imageUrl) return;
    
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `shadefreude-${orientation}-${selectedHexColor.substring(1)}-${new Date().getTime()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
              title="Select Image" 
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
              title="Crop Image" 
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
              title="Pick Color"
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
                    {isGenerating ? 'Generating Card...' : 'Generate Card'}
                  </button>
                </div>
              </WizardStep>
            )}

            {(isCropStepCompleted && (currentWizardStep === 'results' || isGenerating)) && (
              <WizardStep
                title="Claim Your Card"
                stepNumber={4}
                isActive={currentWizardStep === 'results'}
                isCompleted={isResultsStepCompleted}
                onHeaderClick={isStepHeaderClickable('results') ? () => setStep('results') : undefined}
              >
        {isGenerating && (
                  <div className="w-full mb-6">
                    <p className="text-xs text-center text-blue-600 mb-2">
                      Hang on for 20-30 seconds...
                    </p>
            <div className="h-2 w-full bg-muted overflow-hidden rounded">
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
                      {/* Temporarily commented out Share button
                      <button
                        onClick={() => {
                          // Get the current URL for sharing
                          const shareUrl = `${window.location.origin}/card?orientation=${currentDisplayOrientation}&color=${encodeURIComponent(selectedHexColor)}&colorName=${encodeURIComponent(colorNameInput)}`;
                          
                          // Save images to sessionStorage for the share page to access
                          if (generatedHorizontalImageUrl) {
                            sessionStorage.setItem('horizontalCardUrl', generatedHorizontalImageUrl);
                          }
                          if (generatedVerticalImageUrl) {
                            sessionStorage.setItem('verticalCardUrl', generatedVerticalImageUrl);
                          }
                          
                          // Try using the Web Share API if available (mobile devices)
                          if (navigator.share) {
                            navigator.share({
                              title: `${colorNameInput} - Shadefreude Color Card`,
                              text: 'Check out this color card I created with shadefreude!',
                              url: shareUrl
                            })
                            .catch(err => {
                              console.error('Error sharing:', err);
                              // Fallback if sharing fails
                              window.location.href = shareUrl;
                            });
                          } else {
                            // Copy to clipboard on desktop
                            navigator.clipboard.writeText(shareUrl)
                              .then(() => {
                                alert('Share link copied to clipboard!');
                                // Still navigate to the share page
                                window.location.href = shareUrl;
                              })
                              .catch(err => {
                                console.error('Failed to copy:', err);
                                // Fallback - just navigate
                                window.location.href = shareUrl;
                              });
                          }
                        }}
                        disabled={isGenerating || (currentDisplayOrientation === 'horizontal' ? !generatedHorizontalImageUrl : !generatedVerticalImageUrl)}
                        className="px-4 py-2 md:px-6 md:py-3 bg-input text-foreground font-semibold border-2 border-foreground shadow-[4px_4px_0_0_theme(colors.foreground)] hover:shadow-[2px_2px_0_0_theme(colors.foreground)] active:shadow-[1px_1px_0_0_theme(colors.foreground)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                        Share
                      </button>
                      */}
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