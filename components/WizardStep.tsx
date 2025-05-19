'use client';

import React, { useState } from 'react';

interface WizardStepProps {
  title: string;
  stepNumber: number;
  isActive: boolean;
  isCompleted: boolean;
  onHeaderClick?: () => void;
  children: React.ReactNode;
  isFutureStep?: boolean;
}

const WizardStep: React.FC<WizardStepProps> = ({
  title,
  stepNumber,
  isActive,
  isCompleted,
  onHeaderClick,
  children,
  isFutureStep,
}) => {
  // Add state to track expanded/collapsed state
  const [isExpanded, setIsExpanded] = useState(isActive);
  
  // Update isExpanded when isActive changes
  React.useEffect(() => {
    setIsExpanded(isActive);
  }, [isActive]);
  
  let headerClasses = "text-xl font-semibold p-4 flex justify-between items-center";
  if (onHeaderClick && !isFutureStep) headerClasses += " cursor-pointer";

  if (isActive) {
    headerClasses += " bg-secondary text-secondary-foreground";
  } else if (isCompleted) {
    headerClasses += " bg-card text-card-foreground hover:bg-muted";
  } else if (isFutureStep) {
    headerClasses += " bg-card text-muted-foreground cursor-not-allowed";
  } else {
    headerClasses += " bg-card text-card-foreground";
  }

  // Old-school checkmark character: "✓" (could also use "✔" or "☑")
  const oldSchoolCheckmark = "✓";

  // Conditional border: No bottom border for the last step (now step 5)
  const stepWrapperClasses = `${isFutureStep && !isCompleted ? 'opacity-60' : ''} ${stepNumber === 5 ? '' : 'border-b-2 border-foreground'}`;

  // Handle header click to toggle expansion while also calling the original onHeaderClick
  const handleHeaderClick = () => {
    if (!isFutureStep && onHeaderClick) {
      // Toggle expanded state when header is clicked
      setIsExpanded(!isExpanded);
      // Still call the original onHeaderClick to maintain the step navigation
      onHeaderClick();
    }
  };

  return (
    <div className={stepWrapperClasses}>
      <h3
        className={headerClasses}
        onClick={isFutureStep ? undefined : handleHeaderClick}
      >
        <div className="flex items-center">
          <span className="font-semibold">{title}</span>
          {isCompleted && !isActive && 
            <span className="text-[var(--accent-green)] text-2xl leading-none ml-2">{oldSchoolCheckmark}</span>
          }
        </div>
        
        {onHeaderClick && !isFutureStep && (isExpanded ? '[-]' : '[+]')}
      </h3>
      {isExpanded && <div className="p-4 md:p-6 space-y-6 bg-card">{children}</div>}
    </div>
  );
};

export default WizardStep; 