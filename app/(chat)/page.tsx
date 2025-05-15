'use client';

import ImageUpload from '@/components/ImageUpload';
import ColorTools from '@/components/ColorTools';
import { useState } from 'react';

export default function HomePage() {
  const [croppedImageDataUrl, setCroppedImageDataUrl] = useState<string | null>(null);
  const [selectedHexColor, setSelectedHexColor] = useState<string>('#000000');
  const [colorName, setColorName] = useState<string>('');

  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  const handleImageSelected = (file: File) => {
    setCroppedImageDataUrl(null); 
    setSelectedHexColor('#000000');
    setGeneratedImageUrl(null); 
    setGenerationError(null);
    console.log('New original image selected:', file.name); 
  };

  const handleImageCropped = (dataUrl: string | null) => {
    setCroppedImageDataUrl(dataUrl);
    setGeneratedImageUrl(null); 
    setGenerationError(null);
  };

  const handleHexColorChange = (hex: string) => {
    setSelectedHexColor(hex);
    setGeneratedImageUrl(null); 
  };

  const handleColorNameChange = (name: string) => {
    setColorName(name);
    setGeneratedImageUrl(null); 
  };

  const handleGenerateImageClick = async () => {
    if (!croppedImageDataUrl || !selectedHexColor || !colorName.trim()) {
      setGenerationError('Please ensure an image is cropped, a HEX color is set, and a color name is provided.');
      return;
    }
    setIsGenerating(true);
    setGenerationError(null);
    setGeneratedImageUrl(null);

    try {
      // The API route is /api/generate-image as defined in sf/api/index.py
      // and next.config.js rewrites /api/* to the python backend.
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          croppedImageDataUrl,
          hexColor: selectedHexColor,
          colorName,
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

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-6 md:p-12 bg-gray-100 dark:bg-gray-900">
      <div className="w-full max-w-4xl space-y-10">
        <header className="py-6">
          <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-800 dark:text-gray-100">
            shadenfreude
          </h1>
        </header>

        <section className="w-full bg-white dark:bg-gray-800 shadow-2xl rounded-xl p-6 md:p-10 space-y-8 ring-1 ring-gray-200 dark:ring-gray-700">
          <ImageUpload 
            onImageSelect={handleImageSelected} 
            onImageCropped={handleImageCropped} 
          />

          <ColorTools 
            initialHex={selectedHexColor}
            initialName={colorName}
            onHexChange={handleHexColorChange}
            onNameChange={handleColorNameChange}
            croppedImageDataUrl={croppedImageDataUrl}
          />
          
          <div className="pt-6 border-t border-gray-200 dark:border-gray-700 space-y-4">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100">Generate Card:</h3>
              <button
                onClick={handleGenerateImageClick}
                disabled={!croppedImageDataUrl || !colorName.trim() || isGenerating}
                className="w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md 
                           hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 
                           disabled:opacity-60 disabled:cursor-not-allowed
                           dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors duration-150"
              >
                {isGenerating ? 'Generating...' : 'Generate Shadenfreude Card'}
              </button>
              {generationError && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-2">Error: {generationError}</p>
              )}
          </div>

          {generatedImageUrl && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-4">Generated Image:</h3>
              <img 
                src={generatedImageUrl} 
                alt="Generated Shadenfreude card" 
                className="max-w-full h-auto rounded-lg border border-gray-300 dark:border-gray-600 shadow-lg"
                onLoad={() => { if (generatedImageUrl) URL.revokeObjectURL(generatedImageUrl); }} 
              />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
