'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'results' | 'download';

export default function HomePage() {
  const [uploadStepPreviewUrl, setUploadStepPreviewUrl] = useState<string | null>(null);
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [generatedVerticalImageUrl, setGeneratedVerticalImageUrl] = useState<string | null>(null);
  const [generatedHorizontalImageUrl, setGeneratedHorizontalImageUrl] = useState<string | null>(null);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'horizontal' | 'vertical'>('horizontal');
  const [confirmedOrientation, setConfirmedOrientation] = useState<'horizontal' | 'vertical' | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorNameInput, setColorNameInput] = useState<string>('OLIVE ALPINE SENTINEL');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const [userHasInteractedWithColor, setUserHasInteractedWithColor] = useState(false);

  // State for wizard completion
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  const [isResultsStepCompleted, setIsResultsStepCompleted] = useState(false);
  
  // Scroll to the active step or results
  useEffect(() => {
    if (currentWizardStep === 'results' || currentWizardStep === 'download') {
      resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [currentWizardStep]);

  useEffect(() => {
    let urlsToRevoke: string[] = [];
    // We only want to revoke the URLs that are currently *not* being displayed
    // or if we are resetting everything.
    // This effect should primarily run when generatedVerticalImageUrl or generatedHorizontalImageUrl change.

    // This logic might be too aggressive if it runs every time generatedImageUrl changes due to toggling.
    // Let's refine it to only revoke when a *new* set of images is generated (i.e., when isGenerating becomes false)
    // OR when the component unmounts.

    // For now, the existing dependency array [generatedImageUrl, generatedVerticalImageUrl, generatedHorizontalImageUrl]
    // means it will try to revoke whenever *any* of these change. This could be an issue if toggling re-triggers it.
    // A better approach would be to revoke old URLs inside resetGeneration or when new images are fetched.

    // For simplicity, let's stick to revoking only when the component unmounts for now.
    // The resetGeneration function already handles revoking.
    // return () => {
    //   if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    //   if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    //   if (generatedImageUrl?.startsWith('blob:') && 
    //       generatedImageUrl !== generatedVerticalImageUrl && 
    //       generatedImageUrl !== generatedHorizontalImageUrl) {
    //     URL.revokeObjectURL(generatedImageUrl);
    //   }
    // };
  }, []); // Empty dependency array means this cleanup runs only on unmount

  const resetWizard = () => {
    setUploadStepPreviewUrl(null);
    setCroppedImageDataUrl(null);
    setSelectedHexColor('#000000');
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    setCurrentDisplayOrientation('horizontal');
    setConfirmedOrientation(null);
    setIsGenerating(false);
    setGenerationError(null);
    setColorNameInput('OLIVE ALPINE SENTINEL');
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

  const handleImageCropped = (dataUrl: string | null) => {
    setCroppedImageDataUrl(dataUrl);
    // When image is cropped, reset subsequent steps' progress
    setIsColorStepCompleted(false);
    setIsResultsStepCompleted(false);
    setConfirmedOrientation(null);
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
        setConfirmedOrientation(null);
        setCurrentWizardStep('color'); // Stay to regenerate
    }
  };

  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor || !userHasInteractedWithColor) {
      setGenerationError('Please ensure an image is cropped and a color has been actively selected.');
      return;
    }
    
    setIsGenerating(true);
    setGenerationError(null);
    setGenerationProgress(0);
    // Clear previous images before new generation
    if (generatedVerticalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedVerticalImageUrl);
    if (generatedHorizontalImageUrl?.startsWith('blob:')) URL.revokeObjectURL(generatedHorizontalImageUrl);
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    
    let tempHorizontalUrl: string | null = null;
    let tempVerticalUrl: string | null = null;

    try {
      setGenerationProgress(10);
      const horizontalResponse = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          croppedImageDataUrl: croppedImageDataUrl,
          hexColor: selectedHexColor,
          colorName: colorNameInput,
          orientation: 'horizontal',
        }),
      });
      if (!horizontalResponse.ok) {
        const errorText = await horizontalResponse.text();
        throw new Error(`Horizontal card generation failed: ${errorText.substring(0,150)}`);
      }
      const horizontalBlob = await horizontalResponse.blob();
      tempHorizontalUrl = URL.createObjectURL(horizontalBlob);
      setGeneratedHorizontalImageUrl(tempHorizontalUrl);
      setGenerationProgress(50);

      const verticalResponse = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          croppedImageDataUrl: croppedImageDataUrl,
          hexColor: selectedHexColor,
          colorName: colorNameInput,
          orientation: 'vertical',
        }),
      });
      if (!verticalResponse.ok) {
        const errorText = await verticalResponse.text();
        setGenerationError(`Vertical card generation failed: ${errorText.substring(0,150)}. Horizontal version is available.`);
        // Not throwing, allowing horizontal to proceed
      } else {
        const verticalBlob = await verticalResponse.blob();
        tempVerticalUrl = URL.createObjectURL(verticalBlob);
        setGeneratedVerticalImageUrl(tempVerticalUrl);
      }
      
      setIsColorStepCompleted(true); // Mark step 3 complete
      setCurrentWizardStep('results'); // Move to step 4
      setGenerationProgress(100);

    } catch (error) {
      console.error('Error during image generation:', error);
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred.');
      if (tempHorizontalUrl) URL.revokeObjectURL(tempHorizontalUrl);
      if (tempVerticalUrl) URL.revokeObjectURL(tempVerticalUrl);
      setGeneratedHorizontalImageUrl(null); 
      setGeneratedVerticalImageUrl(null);
      setIsColorStepCompleted(false); // Generation failed, so color step not truly done for advancing
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirmOrientation = () => {
    if (!currentDisplayOrientation) return; // Should not happen if in results step with images
    setConfirmedOrientation(currentDisplayOrientation);
    setIsResultsStepCompleted(true);
    setCurrentWizardStep('download');
  };

  const setStep = (step: WizardStepName) => {
    // Basic forward navigation only if prerequisites met
    if (step === 'upload') setCurrentWizardStep('upload');
    else if (step === 'crop' && isUploadStepCompleted) setCurrentWizardStep('crop');
    else if (step === 'color' && isCropStepCompleted) setCurrentWizardStep('color');
    else if (step === 'results' && isColorStepCompleted) setCurrentWizardStep('results');
    else if (step === 'download' && isResultsStepCompleted) setCurrentWizardStep('download');
  };
  
  // Helper to determine if a step header should be clickable (i.e., it's a past, completed step)
  const isStepHeaderClickable = (stepName: WizardStepName): boolean => {
    if (stepName === 'upload' && (isUploadStepCompleted || currentWizardStep === 'upload')) return true;
    if (stepName === 'crop' && (isCropStepCompleted || (currentWizardStep === 'crop' && isUploadStepCompleted))) return true;
    if (stepName === 'color' && (isColorStepCompleted || (currentWizardStep === 'color' && isCropStepCompleted))) return true;
    if (stepName === 'results' && (isResultsStepCompleted || (currentWizardStep === 'results' && isColorStepCompleted))) return true;
    // Download step is not typically navigated back to via header click once confirmed
    return false;
  };

  const handleDownloadImage = (orientation: 'vertical' | 'horizontal' = 'vertical') => {
    const imageUrl = orientation === 'vertical' ? generatedVerticalImageUrl : generatedHorizontalImageUrl;
    if (!imageUrl) return;
    
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `shadefreude-${orientation}-${colorNameInput.toLowerCase().replace(/\s+/g, '-')}-${new Date().getTime()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
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
                onImageCropped={handleImageCropped}
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
                <ImageUpload 
                  onImageSelect={() => {}} 
                  onImageCropped={handleImageCropped} 
                  showUploader={false}
                  showCropper={true}
                  initialPreviewUrl={uploadStepPreviewUrl}
                  aspectRatio={5/6}
                  key={`cropper-${uploadStepPreviewUrl}`}
                />
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
                  onColorPickedFromCanvas={() => setUserHasInteractedWithColor(true)}
                />
                <p className="text-sm text-center text-muted-foreground mt-4 mb-2">
                  Click on the image to pick the color.
                </p>
                <div className="flex justify-center w-full gap-4 mt-2">
                  <button
                    onClick={handleGenerateImageClick}
                    disabled={!croppedImageDataUrl || !selectedHexColor || isGenerating || !userHasInteractedWithColor}
                    className="px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/><path d="M5 6v4"/><path d="M19 14v4"/><path d="M10 2v2"/><path d="M7 8H3"/><path d="M21 16h-4"/></svg>
                    {isGenerating ? 'Generating Card...' : 'Generate Card'}
                  </button>
                </div>
              </WizardStep>
            )}

            {isColorStepCompleted && (
              <WizardStep
                title="Choose Orientation"
                stepNumber={4}
                isActive={currentWizardStep === 'results'}
                isCompleted={isResultsStepCompleted}
                onHeaderClick={isStepHeaderClickable('results') ? () => setStep('results') : undefined}
              >
                {(generatedHorizontalImageUrl || generatedVerticalImageUrl) ? (
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
                        <img src={generatedHorizontalImageUrl} alt="Generated horizontal card" className={`max-w-full rounded-md md:max-w-xl h-auto shadow-lg`} />
                      ) : (currentDisplayOrientation === 'vertical' && generatedVerticalImageUrl) ? (
                        <img src={generatedVerticalImageUrl} alt="Generated vertical card" className={`max-w-full rounded-md md:max-w-xs max-h-[70vh] h-auto shadow-lg`} />
                      ) : (
                        <p className="text-muted-foreground">Select an orientation to view.</p>
                      )}
                    </div>
                    <button
                      onClick={handleConfirmOrientation}
                      disabled={isGenerating || (currentDisplayOrientation === 'horizontal' ? !generatedHorizontalImageUrl : !generatedVerticalImageUrl) }
                      className="mt-4 px-6 py-3 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                    >
                       <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                       Confirm Orientation
                    </button>
                  </div>
                ) : (
                  <p className="text-muted-foreground p-4 text-center">Card images are being generated or an error occurred. Please wait or check error messages.</p>
                )}
              </WizardStep>
            )}

            {isResultsStepCompleted && confirmedOrientation && (
              <WizardStep
                title="Download Your Card"
                stepNumber={5}
                isActive={currentWizardStep === 'download'}
                isCompleted={false}
                onHeaderClick={undefined}
              >
                <div className="space-y-4 flex flex-col items-center">
                  <p className="text-lg font-medium">Your unique card is ready!</p>
                  <div className="flex justify-center w-full">
                     {(confirmedOrientation === 'horizontal' && generatedHorizontalImageUrl) ? (
                        <img src={generatedHorizontalImageUrl} alt="Confirmed horizontal card" className={`max-w-full rounded-md md:max-w-xl h-auto shadow-lg`} />
                      ) : (confirmedOrientation === 'vertical' && generatedVerticalImageUrl) ? (
                        <img src={generatedVerticalImageUrl} alt="Confirmed vertical card" className={`max-w-full rounded-md md:max-w-xs max-h-[70vh] h-auto shadow-lg`} />
                      ) : null}
                  </div>
                  <button
                      onClick={() => handleDownloadImage(confirmedOrientation)}
                      className="px-3 py-2 md:px-4 md:py-2 bg-white text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000] hover:shadow-[2px_2px_0_0_#000] active:shadow-[1px_1px_0_0_#000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 text-sm md:text-base disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:border-muted-foreground"
                  >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                      Download Card
                  </button>
                  <button
                      onClick={resetWizard}
                      className="mt-6 px-4 py-2 text-sm text-muted-foreground hover:text-foreground underline"
                  >
                      Create New Card
                  </button>
                </div>
              </WizardStep>
            )}
          </section>
        </div>
        
        {isGenerating && currentWizardStep !=='results' && currentWizardStep !=='download' && (
          <div className="w-full bg-background p-4 rounded-md border-2 border-foreground mt-6">
            <p className="text-sm text-center mb-2">Generating card... please wait.</p>
            <div className="h-2 w-full bg-muted overflow-hidden rounded">
              <div 
                className="h-full bg-blue-700 transition-all duration-500 ease-in-out" 
                style={{ width: `${generationProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {generationError && (
          <div className="w-full bg-destructive/10 text-destructive p-4 rounded-md border-2 border-destructive mt-6">
            <div className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span className="font-medium">Error:</span>
            </div>
            <p className="mt-1 ml-7 text-sm">{generationError}</p>
          </div>
        )}
      </div>
    </main>
  );
}