import React, { useState } from "react";

const EXAMPLE_PROMPTS = [
  "Three-tier web app on AWS with ALB, ECS, and Aurora PostgreSQL",
  "AWS Lambda behind API Gateway writing to DynamoDB",
  "Kubernetes cluster with ingress, services, and persistent volumes",
  "Multi-region deployment on GCP with Cloud Load Balancing",
];

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  isLoading?: boolean;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onSubmit(prompt.trim());
    }
  };

  return (
    <div className="flex flex-col gap-3 p-4">
      <form onSubmit={handleSubmit} className="flex flex-col gap-2">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your architecture..."
          className="w-full resize-none rounded-lg border border-gray-300 p-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          rows={3}
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={!prompt.trim() || isLoading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isLoading ? "Generating..." : "Generate Diagram"}
        </button>
      </form>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-gray-500">Examples:</span>
        {EXAMPLE_PROMPTS.map((example) => (
          <button
            key={example}
            onClick={() => setPrompt(example)}
            className="text-left text-xs text-blue-600 hover:text-blue-800 hover:underline"
            disabled={isLoading}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  );
};
