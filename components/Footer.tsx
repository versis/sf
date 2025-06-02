"use client";

import React, { useState } from 'react';
import { Copy, ExternalLink } from 'lucide-react';

const Footer = () => {
  const [tooltipText, setTooltipText] = useState("click to copy");

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setTooltipText("copied!");
      setTimeout(() => {
        setTooltipText("click to copy");
      }, 2000);
    }).catch(err => {
      console.error('Failed to copy: ', err);
      setTooltipText("failed to copy");
      setTimeout(() => {
        setTooltipText("click to copy");
      }, 2000);
    });
  };

  return (
    <footer className="text-center py-4 text-xs md:text-sm mt-8 px-6 md:px-12">
      <div className="w-full max-w-6xl mx-auto">
        <div className="border-t-2 border-foreground" />
      </div>
      <div className="w-full max-w-6xl mx-auto mt-4 flex flex-col md:flex-row justify-center items-center space-y-2 md:space-y-0 md:space-x-2">
        <span>
          &copy; {new Date().getFullYear()} <a href="https://tinker.institute" target="_blank" rel="noopener noreferrer" className="hover:underline">tinker.institute</a>
        </span>
        <span className="hidden md:inline">|</span>
        <span>Made in Poland</span>
        <span className="hidden md:inline">|</span>
        <div 
          id="email-container" 
          className="email-container relative flex items-center cursor-pointer group bg-gray-100 hover:bg-gray-200 px-2 py-0.5 rounded-md transition-colors"
          onClick={() => copyToClipboard('kuba@tinker.institute')}
          title={tooltipText}
        >
          <Copy className="mr-2 h-3 w-3 md:h-4 md:w-4 text-black flex-shrink-0" />
          <span className="copy-email text-xs md:text-sm" id="copy-email">
            kuba@tinker.institute
          </span>
          <span 
            className="absolute -bottom-9 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-black text-white text-xs rounded-none opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10"
          >
            {tooltipText}
          </span>
        </div>
        <span className="hidden md:inline">|</span>
        <span className="text-xs md:text-sm">
          <a 
            href="http://tinker.institute/privacy-policy.txt" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="underline underline-offset-4 inline-flex items-center"
          >
            privacy-policy.txt
            <ExternalLink className="ml-1 h-2 w-2 md:h-3 md:w-3 text-gray-500" />
          </a>
        </span>
      </div>
    </footer>
  );
};

export default Footer; 