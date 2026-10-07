import React from 'react';

interface PredictionCardProps {
  predictedYield: number;
  crop: string;
  season: string;
}

/**
 * "Prediction Card" per Requirement 5 -- shows the headline predicted
 * yield number, large and simple, as the entry point to the farmer
 * assistant panel.
 */
export const PredictionCard: React.FC<PredictionCardProps> = ({ predictedYield, crop, season }) => (
  <div className="card-container border-primary border-l-4">
    <h3 className="font-label-caps text-label-caps uppercase tracking-wider text-on-surface-variant mb-2">
      Predicted Yield
    </h3>
    <div className="flex items-baseline mb-1">
      <span className="font-display-lg text-display-lg text-primary dark:text-primary-fixed mr-2">
        {predictedYield.toFixed(2)}
      </span>
      <span className="font-headline-md text-headline-md text-on-surface-variant">t/ha</span>
    </div>
    <p className="font-body-sm text-body-sm text-on-surface-variant">
      {crop} &middot; {season} season
    </p>
  </div>
);
