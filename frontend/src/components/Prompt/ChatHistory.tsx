/**
 * ChatHistory — display conversation thread of prompts and AI responses.
 */

import React from "react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface ChatHistoryProps {
  messages: ChatMessage[];
}

export const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  if (messages.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 border-t border-gray-200 p-4">
      <h4 className="text-xs font-medium text-gray-500">History</h4>
      <div className="flex max-h-48 flex-col gap-2 overflow-auto">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`rounded p-2 text-xs ${
              msg.role === "user"
                ? "bg-blue-50 text-blue-800"
                : "bg-gray-50 text-gray-700"
            }`}
          >
            <span className="font-medium">
              {msg.role === "user" ? "You" : "AI"}:
            </span>{" "}
            {msg.content}
          </div>
        ))}
      </div>
    </div>
  );
};
