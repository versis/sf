'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import WizardStep from '@/components/WizardStep';
import { useState, useRef, useEffect } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'generate';

export default function HomePage() {
  const [uploadStepPreviewUrl, setUploadStepPreviewUrl] = useState<string | null>(null);
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [generatedVerticalImageUrl, setGeneratedVerticalImageUrl] = useState<string | null>(null);
  const [generatedHorizontalImageUrl, setGeneratedHorizontalImageUrl] = useState<string | null>(null);
  const [currentDisplayOrientation, setCurrentDisplayOrientation] = useState<'vertical' | 'horizontal'>('vertical');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorName, setColorName] = useState<string>('DARK EMBER');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null); // For smooth progress

  // State for wizard
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  
  // Scroll to the result when the card is generated
  useEffect(() => {
    if (generatedImageUrl && resultRef.current && !generatedVerticalImageUrl && !generatedHorizontalImageUrl) {
      resultRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [generatedImageUrl, generatedVerticalImageUrl, generatedHorizontalImageUrl]);

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

  const handleImageSelectedForUpload = (file: File) => {
    console.log(`STEP 1.1: Original file selected - Name: ${file.name}, Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`);
    setSelectedFileName(file.name);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      // Log the size of the data URL
      const sizeInMB = (dataUrl.length * 0.75) / (1024 * 1024);
      console.log(`STEP 1.2: Data URL created from upload - Size: ${sizeInMB.toFixed(2)} MB`);
      
      setUploadStepPreviewUrl(dataUrl);
      setCroppedImageDataUrl(null); 
      setSelectedHexColor('#000000');
      setGeneratedImageUrl(null);
      setGeneratedVerticalImageUrl(null);
      setGeneratedHorizontalImageUrl(null);
      setGenerationError(null);
      setIsUploadStepCompleted(true);
      setIsCropStepCompleted(false);
      setIsColorStepCompleted(false);
      setCurrentWizardStep('crop');
      console.log('New original image selected for upload:', file.name);
    };
    reader.onerror = () => {
      console.error('Error reading file for preview.');
      setGenerationError('Error reading file for preview.');
      // Reset relevant states if file reading fails
      setUploadStepPreviewUrl(null);
      setIsUploadStepCompleted(false);
      setCurrentWizardStep('upload');
    };
    reader.readAsDataURL(file);
  };

  const handleImageCropped = (dataUrl: string | null) => {
    if (dataUrl) {
      // Log the cropped image size
      const sizeInMB = (dataUrl.length * 0.75) / (1024 * 1024);
      console.log(`STEP 2: Image cropped - Size: ${sizeInMB.toFixed(2)} MB`);
    }
    setCroppedImageDataUrl(dataUrl);
    setGeneratedImageUrl(null); 
    setGenerationError(null);
    if (dataUrl) {
      setIsCropStepCompleted(true);
      setCurrentWizardStep('color');
    } else {
      setIsCropStepCompleted(false);
    }
  };

  const handleHexColorChange = (hex: string) => {
    setSelectedHexColor(hex);
    setGeneratedImageUrl(null);
  };
  
  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor) {
      setGenerationError('Please ensure an image is cropped and a HEX color is set.');
      return;
    }
    setCurrentWizardStep('' as any); // Close the wizard
    setGeneratedImageUrl(null); 
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    setCurrentDisplayOrientation('vertical'); // Default to showing vertical first
    setGenerationProgress(0);
    setIsGenerating(true);
    setGenerationError(null);
    setIsColorStepCompleted(true); // Mark color step completed when generating
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    try {
      // STAGE 1: Generate Vertical Card
      let compressedDataForVertical = croppedImageDataUrl;
      try {
        compressedDataForVertical = await compressImage(croppedImageDataUrl, 0.7);
      } catch (compressError) {
        console.warn('Vertical image compression failed, using original:', compressError);
      }
      setGenerationProgress(10);
      
      const verticalResponse = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          croppedImageDataUrl: compressedDataForVertical,
          hexColor: selectedHexColor,
          colorName: colorName || 'DARK EMBER',
          orientation: 'vertical',
        }),
      });

      if (!verticalResponse.ok) {
        const errorText = await verticalResponse.text();
        throw new Error(`Vertical card generation failed: ${verticalResponse.status} ${errorText.substring(0,100)}`);
      }
      const verticalBlob = await verticalResponse.blob();
      const verticalUrl = URL.createObjectURL(verticalBlob);
      setGeneratedVerticalImageUrl(verticalUrl); // Store the vertical URL
      console.log(`STEP 4.1: Received vertical image - Size: ${(verticalBlob.size / (1024 * 1024)).toFixed(2)} MB`);
      setGenerationProgress(50);

      // STAGE 2: Generate Horizontal Card
      let compressedDataForHorizontal = croppedImageDataUrl;
      try {
        compressedDataForHorizontal = await compressImage(croppedImageDataUrl, 0.7);
      } catch (compressError) {
        console.warn('Horizontal image compression failed, using original:', compressError);
      }
      setGenerationProgress(60);

      const horizontalResponse = await fetch('/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          croppedImageDataUrl: compressedDataForHorizontal,
          hexColor: selectedHexColor,
          colorName: colorName || 'DARK EMBER',
          orientation: 'horizontal',
        }),
      });

      if (!horizontalResponse.ok) {
        const errorText = await horizontalResponse.text();
        throw new Error(`Horizontal card generation failed: ${horizontalResponse.status} ${errorText.substring(0,100)}`);
      }
      const horizontalBlob = await horizontalResponse.blob();
      const horizontalUrl = URL.createObjectURL(horizontalBlob);
      setGeneratedHorizontalImageUrl(horizontalUrl); // Store the horizontal URL
      console.log(`STEP 4.2: Received horizontal image - Size: ${(horizontalBlob.size / (1024 * 1024)).toFixed(2)} MB`);
      
      // After both are generated, set generatedImageUrl to null initially.
      // The JSX will pick the correct one based on currentDisplayOrientation (which is 'vertical' by default)
      setGeneratedImageUrl(null); 
      // setCurrentDisplayOrientation('vertical'); // Already set before try block
      setGenerationProgress(100);
      
      if (resultRef.current) resultRef.current.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
      console.error('Error during dual image generation:', error);
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred during generation.');
      setGenerationProgress(0);
    } finally {
      setIsGenerating(false);
    }
  };

  // Reset function for Create Another Card
  const resetGeneration = () => {
    // Clear all image URLs
    setGeneratedImageUrl(null);
    setGeneratedVerticalImageUrl(null);
    setGeneratedHorizontalImageUrl(null);
    setUploadStepPreviewUrl(null);
    setCroppedImageDataUrl(null);
    setSelectedFileName(null);
    
    // Reset other states
    setSelectedHexColor('#000000');
    setGenerationError(null);
    setGenerationProgress(0);
    setCurrentDisplayOrientation('vertical');
    
    // Reset wizard steps
    setIsUploadStepCompleted(false);
    setIsCropStepCompleted(false);
    setIsColorStepCompleted(false);
    setCurrentWizardStep('upload');
    
    // Revoke any object URLs to prevent memory leaks
    if (generatedVerticalImageUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(generatedVerticalImageUrl);
    }
    if (generatedHorizontalImageUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(generatedHorizontalImageUrl);
    }
    if (generatedImageUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(generatedImageUrl);
    }
    
    console.log('All states reset, ready for a new card generation');
  };

  const handleDownloadImage = (orientation: 'vertical' | 'horizontal' = 'vertical') => {
    const imageUrl = orientation === 'vertical' ? generatedVerticalImageUrl : generatedHorizontalImageUrl;
    if (!imageUrl) return;
    
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = `shadefreude-${orientation}-${colorName.toLowerCase().replace(/\s+/g, '-')}-${new Date().getTime()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const setStep = (step: WizardStepName) => {
    if (step === 'upload') setCurrentWizardStep('upload');
    else if (step === 'crop' && isUploadStepCompleted) setCurrentWizardStep('crop');
    else if (step === 'color' && isUploadStepCompleted && isCropStepCompleted) setCurrentWizardStep('color');
    else if (step === 'generate' && isUploadStepCompleted && isCropStepCompleted && isColorStepCompleted) setCurrentWizardStep('generate');
  };

  const compressImage = (dataUrl: string, quality = 0.7): Promise<string> => {
    return new Promise((resolve, reject) => {
      const beforeSizeInMB = (dataUrl.length * 0.75) / (1024 * 1024);
      console.log(`STEP 3.1: Image before compression - Size: ${beforeSizeInMB.toFixed(2)} MB`);
      const img = new window.Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Failed to get canvas context'));
          return;
        }
        ctx.drawImage(img, 0, 0);
        const compressed = canvas.toDataURL('image/jpeg', quality);
        const afterSizeInMB = (compressed.length * 0.75) / (1024 * 1024);
        console.log(`STEP 3.2: Image after compression - Size: ${afterSizeInMB.toFixed(2)} MB (${(quality * 100).toFixed(0)}% quality)`);
        resolve(compressed);
      };
      img.onerror = () => reject(new Error('Failed to load image for compression'));
      img.src = dataUrl;
    });
  };

  const handleToggleOrientationDisplay = () => {
    if (isGenerating || !generatedVerticalImageUrl || !generatedHorizontalImageUrl) return;
    const newOrientation = currentDisplayOrientation === 'vertical' ? 'horizontal' : 'vertical';
    setCurrentDisplayOrientation(newOrientation);
  };

  const completeColorStep = () => {
    if (croppedImageDataUrl && selectedHexColor) {
      setIsColorStepCompleted(true);
      setCurrentWizardStep('generate');
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
      <div className="w-full max-w-6xl space-y-6">
        <header className="py-6 border-b-2 border-foreground">
          <h1 className="text-4xl md:text-5xl font-bold text-center flex items-center justify-center">
            <a href="/" onClick={(e) => { e.preventDefault(); window.location.reload();}} className="flex items-center justify-center cursor-pointer">
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
              isFutureStep={false} // First step is never future
              onHeaderClick={() => setStep('upload')}
            >
              <ImageUpload 
                onImageSelect={handleImageSelectedForUpload} 
                onImageCropped={handleImageCropped}
                showUploader={true}
                showCropper={false}
                initialPreviewUrl={uploadStepPreviewUrl}
                currentFileName={selectedFileName}
                key={uploadStepPreviewUrl || selectedFileName || 'uploader'}
              />
            </WizardStep>

            <WizardStep 
              title="Crop Image" 
              stepNumber={2} 
              isActive={currentWizardStep === 'crop'} 
              isCompleted={isCropStepCompleted}
              isFutureStep={!isUploadStepCompleted} // Future if upload isn't done
              onHeaderClick={() => setStep('crop')}
            >
              {isUploadStepCompleted ? (
                <div className="flex justify-center w-full p-1">
                  <ImageUpload 
                    onImageSelect={() => {}} 
                    onImageCropped={handleImageCropped} 
                    showUploader={false}
                    showCropper={true}
                    initialPreviewUrl={uploadStepPreviewUrl}
                  />
                </div>
              ) : (
                <p className="text-muted-foreground">Please select an image in Step 1 first.</p>
              )}
            </WizardStep>

            <WizardStep 
              title="Pick Color"
              stepNumber={3} 
              isActive={currentWizardStep === 'color'} 
              isCompleted={isColorStepCompleted}
              isFutureStep={!isUploadStepCompleted || !isCropStepCompleted}
              onHeaderClick={() => setStep('color')}
            >
              {isCropStepCompleted ? (
                <>
                  <ColorTools 
                    initialHex={selectedHexColor}
                    onHexChange={handleHexColorChange}
                    croppedImageDataUrl={croppedImageDataUrl}
                  />
                  <div className="flex justify-center w-full">
                    <button
                      onClick={completeColorStep}
                      disabled={!selectedHexColor || (selectedHexColor === '#000000' && !isColorStepCompleted && !croppedImageDataUrl)}
                      className="mt-4 px-4 py-2 md:px-6 md:py-3 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>
                      Confirm Color
                    </button>
                  </div>
                </>
              ) : (
                <p className="text-muted-foreground">Please complete image cropping in Step 2 first.</p>
              )}
            </WizardStep>

            <WizardStep 
              title="Generate Card" 
              stepNumber={4} 
              isActive={currentWizardStep === 'generate'} 
              isCompleted={!!generatedVerticalImageUrl || !!generatedHorizontalImageUrl}
              isFutureStep={!isUploadStepCompleted || !isCropStepCompleted || !isColorStepCompleted}
              onHeaderClick={() => setStep('generate')}
            >
              {isColorStepCompleted ? (
                <div className="space-y-4 flex flex-col items-center">
                  <button
                    onClick={handleGenerateImageClick}
                    disabled={!croppedImageDataUrl || !selectedHexColor || isGenerating || !isCropStepCompleted || !isColorStepCompleted}
                    className="px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/><path d="M5 6v4"/><path d="M19 14v4"/><path d="M10 2v2"/><path d="M7 8H3"/><path d="M21 16h-4"/></svg>
                    {isGenerating ? 'Generating...' : 'Generate Card'}
                  </button>
                </div>
              ) : (
                <p className="text-muted-foreground">Please complete the previous steps.</p>
              )}
            </WizardStep>
          </section>
        </div>
        
        {/* Progress bar now appears below the wizard */}
        {isGenerating && (
          <div className="w-full bg-background p-4 rounded-md border-2 border-foreground">
            <div className="h-2 w-full bg-muted overflow-hidden rounded">
              <div 
                className="h-full bg-blue-700 transition-all duration-500 ease-in-out" 
                style={{ width: `${generationProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Display Generation Error below wizard and progress bar */}
        {generationError && !isGenerating && (
          <div className="w-full bg-destructive/10 text-destructive p-4 rounded-md border-2 border-destructive mt-4">
            <div className="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span className="font-medium">Error:</span>
            </div>
            <p className="mt-1 ml-7 text-sm">{generationError}</p>
          </div>
        )}

        {/* Results Section: Display one image at a time with a toggle button */}
        {(generatedVerticalImageUrl && generatedHorizontalImageUrl) && (
          <section ref={resultRef} className="w-full pt-4">
            {/* Orientation toggle buttons */}
            <div className="flex justify-center gap-6 mb-6">
              <button 
                onClick={() => setCurrentDisplayOrientation('vertical')}
                className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'vertical' ? 'border-blue-700 bg-blue-50' : 'border-gray-300'} flex flex-col items-center transition-all duration-200`}
                title="Vertical Orientation"
                disabled={isGenerating}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="5" y="3" width="14" height="18" rx="2" ry="2" />
                </svg>
                <span className="text-xs mt-1">Vertical</span>
              </button>
              <button
                onClick={() => setCurrentDisplayOrientation('horizontal')}
                className={`p-2 border-2 rounded-md ${currentDisplayOrientation === 'horizontal' ? 'border-blue-700 bg-blue-50' : 'border-gray-300'} flex flex-col items-center transition-all duration-200`}
                title="Horizontal Orientation"
                disabled={isGenerating}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="5" width="18" height="14" rx="2" ry="2" />
                </svg>
                <span className="text-xs mt-1">Horizontal</span>
              </button>
            </div>
            <div className="flex justify-center">
              {(currentDisplayOrientation === 'vertical' && generatedVerticalImageUrl) && (
                <img 
                  src={generatedVerticalImageUrl} 
                  alt={`Generated shadefreude card - vertical`}
                  className={`max-w-full rounded-md md:max-w-2xl h-auto`}
                />
              )}
              {(currentDisplayOrientation === 'horizontal' && generatedHorizontalImageUrl) && (
                <img 
                  src={generatedHorizontalImageUrl} 
                  alt={`Generated shadefreude card - horizontal`}
                  className={`max-w-full rounded-md md:max-w-sm max-h-[80vh] h-auto`}
                />
              )}
            </div>
            <div className="flex flex-wrap justify-center gap-3 mt-8">
              {/* Download button for the currently displayed image */}
              <button
                  onClick={() => handleDownloadImage(currentDisplayOrientation)}
                  disabled={!(currentDisplayOrientation === 'vertical' ? generatedVerticalImageUrl : generatedHorizontalImageUrl)}
                  className="px-3 py-2 md:px-4 md:py-2 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 text-sm md:text-base"
              >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download {currentDisplayOrientation === 'vertical' ? 'Vertical' : 'Horizontal'} Card
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}