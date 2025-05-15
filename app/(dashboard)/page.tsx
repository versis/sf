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
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorName, setColorName] = useState<string>('DARK EMBER');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null); // For smooth progress
  const [cardOrientation, setCardOrientation] = useState<'vertical' | 'horizontal'>('vertical');

  // State for wizard
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false);
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);
  
  // Scroll to the result when the card is generated
  useEffect(() => {
    if (generatedImageUrl && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [generatedImageUrl]);

  // Effect to revoke object URL
  useEffect(() => {
    let objectUrlToRevoke: string | null = null;
    if (generatedImageUrl && generatedImageUrl.startsWith('blob:')) {
      objectUrlToRevoke = generatedImageUrl;
    }

    return () => {
      if (objectUrlToRevoke) {
        URL.revokeObjectURL(objectUrlToRevoke);
        console.log('Revoked object URL:', objectUrlToRevoke);
      }
    };
  }, [generatedImageUrl]);

  const handleImageSelectedForUpload = (file: File) => {
    // Log the original file size
    console.log(`STEP 1.1: Original file selected - Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`);
    
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
  
  const completeColorStep = () => {
    if (croppedImageDataUrl && selectedHexColor) {
        setIsColorStepCompleted(true);
        setCurrentWizardStep('generate');
    }
  };

  const compressImage = (dataUrl: string, quality = 0.7): Promise<string> => {
    return new Promise((resolve, reject) => {
      // Log the size before compression
      const beforeSizeInMB = (dataUrl.length * 0.75) / (1024 * 1024);
      console.log(`STEP 3.1: Image before compression - Size: ${beforeSizeInMB.toFixed(2)} MB`);
      
      const img = new Image();
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
        
        // Convert to JPEG for better compression (even if original was PNG)
        const compressed = canvas.toDataURL('image/jpeg', quality);
        
        // Log the size after compression
        const afterSizeInMB = (compressed.length * 0.75) / (1024 * 1024);
        console.log(`STEP 3.2: Image after compression - Size: ${afterSizeInMB.toFixed(2)} MB (${(quality * 100).toFixed(0)}% quality)`);
        
        resolve(compressed);
      };
      img.onerror = () => reject(new Error('Failed to load image for compression'));
      img.src = dataUrl;
    });
  };

  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor) {
      setGenerationError('Please ensure an image is cropped and a HEX color is set.');
      return;
    }
    
    // Close the last step by setting currentWizardStep to null
    setCurrentWizardStep('' as any);
    
    setGeneratedImageUrl(null);
    setGenerationProgress(0); // Initialize progress to 0
    setIsGenerating(true);
    setStatusMessage('Creating your shadefreude card...');

    // Clear any existing interval
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
    }

    // Smooth progress simulation
    const DURATION = 7000; // Target 7 seconds
    const TICK_INTERVAL = 70; // Update every 70ms
    let currentProgress = 0;

    progressIntervalRef.current = setInterval(() => {
      currentProgress += 1;
      if (currentProgress < 99) { // Stop before 100, actual completion will set it to 100
        setGenerationProgress(currentProgress);
      } else {
        if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      }
    }, TICK_INTERVAL);

    try {
      // Compress the image before sending
      // setGenerationProgress(30); // No longer direct set, rely on interval
      setStatusMessage('Compressing image...');
      let compressedImageDataUrl = croppedImageDataUrl;
      try {
        compressedImageDataUrl = await compressImage(croppedImageDataUrl, 0.7);
        console.log('Image compressed successfully');
      } catch (compressError) {
        console.warn('Image compression failed, using original:', compressError);
      }

      // setGenerationProgress(50); // No longer direct set
      setStatusMessage('Generating card...');
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          croppedImageDataUrl: compressedImageDataUrl,
          hexColor: selectedHexColor,
          colorName: colorName || 'DARK EMBER',
        }),
      });

      if (!response.ok) {
        const errorText = await response.text(); // Get raw error text
        let errorDetail = `Server error: ${response.status} ${response.statusText}`;
        try {
          // Try to parse as JSON, as some errors might still be structured
          const errorData = JSON.parse(errorText);
          errorDetail = errorData.error || errorData.detail || errorText; // Use specific error fields if available
        } catch (e) {
          // If not JSON, use the raw text, truncating if too long for display
          errorDetail = errorText.length > 150 ? errorText.substring(0, 147) + "..." : errorText;
        }
        console.error('Server error response:', errorText); // Log full server error text
        throw new Error(errorDetail);
      }

      // setGenerationProgress(80); // No longer direct set
      setStatusMessage('Finalizing...');
      
      // Get the binary response as a blob
      const imageBlob = await response.blob();
      console.log(`STEP 4: Received image - Size: ${(imageBlob.size / (1024 * 1024)).toFixed(2)} MB`);
      
      // Create blob URLs for both vertical and horizontal from the same image
      const imageUrl = URL.createObjectURL(imageBlob);
      
      // Store the same image URL for both orientations for now
      // When the backend is updated to return different orientations in the future,
      // this code can be modified to use the distinct images
      setGeneratedVerticalImageUrl(imageUrl);
      setGeneratedHorizontalImageUrl(imageUrl);
      
      // Set the displayed image based on current orientation preference
      setGeneratedImageUrl(imageUrl);
      
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current); // Ensure interval is cleared
      setGenerationProgress(100); // Complete
      setStatusMessage('Your shadefreude card is ready!');
      
      // Scroll to result
      if (resultRef.current) {
        resultRef.current.scrollIntoView({ behavior: 'smooth' });
      }

    } catch (error) {
      console.error('Error generating image:', error);
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred.');
      setStatusMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setGenerationProgress(0); // Reset progress on error
    } finally {
      if (progressIntervalRef.current) clearInterval(progressIntervalRef.current); // Safeguard clear
      setIsGenerating(false);
    }
  };
  
  const handleDownloadImage = () => {
    if (!generatedImageUrl) return;
    
    const link = document.createElement('a');
    link.href = generatedImageUrl;
    link.download = `shadefreude-${colorName.toLowerCase().replace(/\s+/g, '-')}-${new Date().getTime()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleToggleOrientationDisplay = () => {
    if (!generatedVerticalImageUrl || !generatedHorizontalImageUrl) return;

    if (cardOrientation === 'vertical') {
      setGeneratedImageUrl(generatedHorizontalImageUrl);
      setCardOrientation('horizontal');
    } else {
      setGeneratedImageUrl(generatedVerticalImageUrl);
      setCardOrientation('vertical');
    }
  };

  const setStep = (step: WizardStepName) => {
    if (step === 'upload') setCurrentWizardStep('upload');
    else if (step === 'crop' && isUploadStepCompleted) setCurrentWizardStep('crop');
    else if (step === 'color' && isUploadStepCompleted && isCropStepCompleted) setCurrentWizardStep('color');
    else if (step === 'generate' && isUploadStepCompleted && isCropStepCompleted && isColorStepCompleted) setCurrentWizardStep('generate');
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start pt-1 px-6 pb-6 md:pt-3 md:px-12 md:pb-12 bg-background text-foreground">
      <div className="w-full max-w-6xl space-y-10">
        <header className="py-6 border-b-2 border-foreground">
          <h1 className="text-4xl md:text-5xl font-bold text-center flex items-center justify-center">
            <span className="mr-1 ml-1">
              <img src="/sf-icon.png" alt="SF Icon" className="inline h-8 w-8 md:h-12 md:w-12 mr-1" />
              shade
            </span>
            <span className="inline-block bg-card text-foreground border-2 border-blue-700 shadow-[5px_5px_0_0_theme(colors.blue.700)] px-2 py-0.5 mr-1">
              freude
            </span>
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
                key={uploadStepPreviewUrl || 'uploader'}
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
                <div className="flex justify-center w-full">
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
              isFutureStep={!isUploadStepCompleted || !isCropStepCompleted} // Future if upload or crop isn't done
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
              isCompleted={!!generatedImageUrl}
              isFutureStep={!isUploadStepCompleted || !isCropStepCompleted || !isColorStepCompleted} // Future if any prior step isn't done
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
            <div className="mb-2 flex justify-between text-sm font-medium">
              <span>{statusMessage}</span>
              <span>{generationProgress}%</span>
            </div>
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

        {generatedImageUrl && (
          <section ref={resultRef} className="w-full pt-6">
            {/* Button to toggle display orientation - placed above the image */}
            {(generatedVerticalImageUrl && generatedHorizontalImageUrl) && (
              <div className="flex justify-center mb-4">
                <button
                  onClick={handleToggleOrientationDisplay}
                  className="px-3 py-1.5 md:px-4 md:py-2 bg-input text-sm text-black font-medium border-2 border-black shadow-[3px_3px_0_0_#000000] hover:shadow-[1px_1px_0_0_#000000] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] transition-all duration-100 ease-in-out flex items-center gap-2"
                >
                  {cardOrientation === 'vertical' ? (
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="12" x2="21" y2="12"/></svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="12" y1="3" x2="12" y2="21"/></svg>
                  )}
                  View {cardOrientation === 'vertical' ? 'Horizontal' : 'Vertical'} Version
                </button>
              </div>
            )}
            <div className="flex justify-center">
              <img 
                src={generatedImageUrl} 
                alt="Generated shadefreude card" 
                className="max-w-full md:max-w-2xl h-auto rounded-md"
              />
            </div>
            <div className="flex flex-wrap justify-center gap-3 mt-6">
              <button
                onClick={handleDownloadImage}
                className="px-3 py-2 md:px-4 md:py-2 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 text-sm md:text-base"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download Card
              </button>
              <button
                onClick={() => {
                  setGeneratedImageUrl(null);
                  setGeneratedVerticalImageUrl(null); // Also clear specific orientation URLs
                  setGeneratedHorizontalImageUrl(null);
                  setCurrentWizardStep('upload');
                }}
                className="px-3 py-2 md:px-4 md:py-2 bg-input text-black font-semibold border-2 border-black shadow-[4px_4px_0_0_#000000] hover:shadow-[2px_2px_0_0_#000000] active:shadow-[1px_1px_0_0_#000000] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out flex items-center gap-2 text-sm md:text-base"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
                Create Another Card
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
