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
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [colorName, setColorName] = useState<string>('DARK EMBER');
  const [generationProgress, setGenerationProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

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

  const handleImageSelectedForUpload = (file: File) => {
    // Log the original file size
    console.log(`Original file size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`);
    
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = reader.result as string;
      // Log the size of the data URL
      const sizeInMB = (dataUrl.length * 0.75) / (1024 * 1024);
      console.log(`Uploaded image data URL size: ${sizeInMB.toFixed(2)} MB`);
      
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
      console.log(`Cropped image size: ${sizeInMB.toFixed(2)} MB`);
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
      console.log(`Before compression size: ${beforeSizeInMB.toFixed(2)} MB`);
      
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
        console.log(`After compression size: ${afterSizeInMB.toFixed(2)} MB (${(quality * 100).toFixed(0)}% quality)`);
        
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
    
    setIsGenerating(true);
    setGenerationError(null);
    setGeneratedImageUrl(null);
    setGenerationProgress(10); // Start progress at 10%
    setStatusMessage('Creating your shadefreude card...');
    
    try {
      // Compress the image before sending
      setGenerationProgress(30); // Update progress
      setStatusMessage('Compressing image...');
      let compressedImageDataUrl = croppedImageDataUrl;
      try {
        compressedImageDataUrl = await compressImage(croppedImageDataUrl, 0.7);
        console.log('Image compressed successfully');
      } catch (compressError) {
        console.warn('Image compression failed, using original:', compressError);
      }

      setGenerationProgress(50); // Update progress
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

      setGenerationProgress(80); // Update progress
      setStatusMessage('Finalizing...');
      const imageBlob = await response.blob();
      // Log the final card size
      console.log(`Final card size: ${(imageBlob.size / (1024 * 1024)).toFixed(2)} MB`);
      
      const imageUrl = URL.createObjectURL(imageBlob);
      setGeneratedImageUrl(imageUrl);
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
    } finally {
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
                <ImageUpload 
                  onImageSelect={() => {}} 
                  onImageCropped={handleImageCropped} 
                  showUploader={false}
                  showCropper={true}
                  initialPreviewUrl={uploadStepPreviewUrl}
                />
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
                  
                  {/* Alternative icons for Confirm Color button */}
                  <div className="mt-6 p-3 border border-dashed border-muted-foreground rounded-md">
                    <p className="text-sm mb-2 text-muted-foreground">Alternative icons for Confirm Color button:</p>
                    <div className="flex flex-wrap gap-4 justify-center">
                      {/* 1. Color palette */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="19" cy="12" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="8" cy="18" r="2.5"/><line x1="12" y1="22" x2="12" y2="12"/><line x1="12" y1="12" x2="17.5" y2="6.5"/><line x1="12" y1="12" x2="8" y2="18"/><line x1="12" y1="12" x2="19" y2="12"/><line x1="12" y1="12" x2="6" y2="12"/></svg>
                      
                      {/* 2. Droplet */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>
                      
                      {/* 3. Check/Checkmark */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><polyline points="20 6 9 17 4 12"/></svg>
                      
                      {/* 4. Paint bucket */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="m19 11-8-8-8.6 8.6a2 2 0 0 0 0 2.8l5.2 5.2c.8.8 2 .8 2.8 0L19 11Z"/><path d="m5 2 5 5"/><path d="M2 13h15"/><path d="M22 20a2 2 0 1 1-4 0c0-1.6 1.7-2.4 2-4 .3 1.6 2 2.4 2 4Z"/></svg>
                      
                      {/* 5. Save icon */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                      
                      {/* 6. Thumbs up */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/></svg>
                      
                      {/* 7. Color swatch */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><rect width="8" height="8" x="3" y="3" rx="2"/><path d="M7 11v4a2 2 0 0 0 2 2h4"/><rect width="8" height="8" x="13" y="13" rx="2"/></svg>
                      
                      {/* 8. Eye (preview) */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                      
                      {/* 9. Arrow right (next) */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                      
                      {/* 10. Star */}
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="cursor-pointer hover:text-blue-700"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                    </div>
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
                  <div className="w-full max-w-[38.4rem] mb-4">
                    <label htmlFor="colorName" className="block text-sm font-medium text-foreground mb-1">
                      Color Name:
                    </label>
                    <input
                      type="text"
                      id="colorName"
                      value={colorName}
                      onChange={(e) => setColorName(e.target.value)}
                      placeholder="e.g., DARK EMBER"
                      className="w-full p-2 border border-foreground focus:outline-none focus:ring-1 focus:ring-blue-700"
                    />
                  </div>
                  <button
                    onClick={handleGenerateImageClick}
                    disabled={!croppedImageDataUrl || !selectedHexColor || isGenerating || !isCropStepCompleted || !isColorStepCompleted}
                    className="px-4 py-2 md:px-6 md:py-3 bg-input text-blue-700 font-semibold border-2 border-blue-700 shadow-[4px_4px_0_0_theme(colors.blue.700)] hover:shadow-[2px_2px_0_0_theme(colors.blue.700)] active:shadow-[1px_1px_0_0_theme(colors.blue.700)] active:translate-x-[2px] active:translate-y-[2px] transition-all duration-100 ease-in-out disabled:opacity-60 disabled:cursor-not-allowed disabled:shadow-none disabled:text-muted-foreground disabled:border-muted-foreground flex items-center gap-2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.64 3.64-1.28-1.28a1.21 1.21 0 0 0-1.72 0L2.36 18.64a1.21 1.21 0 0 0 0 1.72l1.28 1.28a1.2 1.2 0 0 0 1.72 0L21.64 5.36a1.2 1.2 0 0 0 0-1.72Z"/><path d="m14 7 3 3"/><path d="M5 6v4"/><path d="M19 14v4"/><path d="M10 2v2"/><path d="M7 8H3"/><path d="M21 16h-4"/><path d="M11 3H9"/></svg>
                    {isGenerating ? 'Generating...' : 'Generate Card'}
                  </button>
                  {generationError && (
                    <p className="text-sm text-destructive mt-2">Error: {generationError}</p>
                  )}
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

        {generatedImageUrl && (
          <section ref={resultRef} className="w-full pt-6 border-t-2 border-foreground">
            <div className="flex justify-center">
              <img 
                src={generatedImageUrl} 
                alt="Generated shadefreude card" 
                className="max-w-full md:max-w-2xl h-auto rounded-lg"
                onLoad={() => { if (generatedImageUrl) URL.revokeObjectURL(generatedImageUrl); }} 
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
