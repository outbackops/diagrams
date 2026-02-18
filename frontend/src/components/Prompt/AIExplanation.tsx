import React from "react";

interface AIExplanationProps {
  explanation: string;
  assumptions: string[];
  warnings: string[];
  modelUsed?: string;
}

export const AIExplanation: React.FC<AIExplanationProps> = ({
  explanation,
  assumptions,
  warnings,
  modelUsed,
}) => {
  if (!explanation && assumptions.length === 0 && warnings.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2 border-t border-gray-200 p-4 text-sm">
      {explanation && (
        <div>
          <h4 className="font-medium text-gray-700">AI Explanation</h4>
          <p className="text-gray-600">{explanation}</p>
        </div>
      )}

      {assumptions.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700">Assumptions</h4>
          <ul className="list-inside list-disc text-gray-600">
            {assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {warnings.length > 0 && (
        <div>
          <h4 className="font-medium text-amber-700">Warnings</h4>
          <ul className="list-inside list-disc text-amber-600">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {modelUsed && (
        <p className="text-xs text-gray-400">Model: {modelUsed}</p>
      )}
    </div>
  );
};
