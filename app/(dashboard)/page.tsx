'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import CardPreview from '@/components/CardPreview';
import WizardStep from '@/components/WizardStep';
import { useState } from 'react';

// Define types for wizard steps
type WizardStepName = 'upload' | 'crop' | 'color' | 'generate';

export default function HomePage() {
  const [uploadStepPreviewUrl, setUploadStepPreviewUrl] = useState<string | null>(null);
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // State for wizard
  const [currentWizardStep, setCurrentWizardStep] = useState<WizardStepName>('upload');
  const [isUploadStepCompleted, setIsUploadStepCompleted] = useState(false);
  const [isCropStepCompleted, setIsCropStepCompleted] = useState(false); // Renamed from isImageStepCompleted
  const [isColorStepCompleted, setIsColorStepCompleted] = useState(false);

  const handleImageSelectedForUpload = (file: File) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      setUploadStepPreviewUrl(reader.result as string);
      setCroppedImageDataUrl(null); // Reset crop if new image is selected
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

  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor) {
      setGenerationError('Please ensure an image is cropped and a HEX color is set.');
      return;
    }
    setIsGenerating(true);
    setGenerationError(null);
    setGeneratedImageUrl(null);

    try {
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          croppedImageDataUrl,
          hexColor: selectedHexColor,
          colorName: selectedHexColor, // Placeholder for backend
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Failed to generate image. Server returned an error.' }));
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }

      const imageBlob = await response.blob();
      const imageUrl = URL.createObjectURL(imageBlob);
      setGeneratedImageUrl(imageUrl);

    } catch (error) {
      console.error('Error generating image:', error);
      setGenerationError(error instanceof Error ? error.message : 'An unknown error occurred.');
    } finally {
      setIsGenerating(false);
    }
  };

  const setStep = (step: WizardStepName) => {
    if (step === 'upload') setCurrentWizardStep('upload');
    else if (step === 'crop' && isUploadStepCompleted) setCurrentWizardStep('crop');
    else if (step === 'color' && isUploadStepCompleted && isCropStepCompleted) setCurrentWizardStep('color');
    else if (step === 'generate' && isUploadStepCompleted && isCropStepCompleted && isColorStepCompleted) setCurrentWizardStep('generate');
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 md:p-12 bg-background text-foreground">
      <div className="w-full max-w-6xl space-y-10">
        <header className="py-6 border-b-2 border-foreground">
          <h1 className="text-4xl md:text-5xl font-bold text-center">
            shadenfreude <span className="text-xl md:text-2xl font-normal text-muted-foreground">(sf.tinker.institute)</span>
          </h1>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
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
              title="Pick Background Color" 
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
                  <button 
                      onClick={completeColorStep}
                      disabled={!selectedHexColor || (selectedHexColor === '#000000' && !isColorStepCompleted && !croppedImageDataUrl) }
                      className="mt-4 w-full px-6 py-3 bg-foreground text-background font-semibold border border-foreground hover:bg-opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-ring disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                  >
                      Confirm Color
                  </button>
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
                <div className="space-y-4">
                  <button
                    onClick={handleGenerateImageClick}
                    disabled={!croppedImageDataUrl || !selectedHexColor || isGenerating || !isCropStepCompleted || !isColorStepCompleted}
                    className="w-full px-6 py-3 bg-foreground text-background font-semibold border border-foreground hover:bg-opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-ring disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
                  >
                    {isGenerating ? 'Generating...' : 'Generate Shadenfreude Card'}
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

          <aside className="w-full space-y-6 md:order-2">
            <CardPreview 
              imageDataUrl={croppedImageDataUrl} 
              backgroundColor={selectedHexColor}
            />
          </aside>
        </div>

        {generatedImageUrl && (
          <section className="w-full mt-12 pt-6 border-t-2 border-foreground">
            <h3 className="text-2xl font-semibold text-foreground mb-6 text-center">Your unique Shadenfreude card</h3>
            <div className="flex justify-center">
              <img 
                src={generatedImageUrl} 
                alt="Generated Shadenfreude card" 
                className="max-w-full md:max-w-2xl h-auto rounded-lg"
                onLoad={() => { if (generatedImageUrl) URL.revokeObjectURL(generatedImageUrl); }} 
              />
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
