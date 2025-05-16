'use client';

import React from 'react';

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

  return (
    <div className={stepWrapperClasses}>
      <h3
        className={headerClasses}
        onClick={isFutureStep ? undefined : onHeaderClick}
      >
        <div className="flex items-center">
          <span className="font-semibold">Step {stepNumber}:&nbsp;</span>
          <span className="font-semibold">{title}</span>
          {isCompleted && !isActive && 
            <span className="text-[var(--accent-green)] text-2xl leading-none ml-2">{oldSchoolCheckmark}</span>
          }
        </div>
        
        {onHeaderClick && !isFutureStep && (isActive ? '[-]' : '[+]')}
      </h3>
      {isActive && <div className="p-4 md:p-6 space-y-6 bg-card">{children}</div>}
    </div>
  );
};

export default WizardStep; 