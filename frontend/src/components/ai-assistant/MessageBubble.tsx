"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/lib/types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={cn(
        "flex gap-3",
        isAssistant ? "flex-row" : "flex-row-reverse"
      )}
    >
      <Avatar className="h-8 w-8 flex-shrink-0">
        <AvatarFallback
          className={cn(
            isAssistant ? "bg-primary text-primary-foreground" : "bg-muted"
          )}
        >
          {isAssistant ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "flex flex-col max-w-[80%]",
          isAssistant ? "items-start" : "items-end"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-2",
            isAssistant
              ? "bg-muted rounded-tl-none"
              : "bg-primary text-primary-foreground rounded-tr-none"
          )}
        >
          <div
            className={cn(
              "text-sm whitespace-pre-wrap",
              isAssistant && "prose prose-sm dark:prose-invert max-w-none"
            )}
          >
            {formatMessage(message.content)}
          </div>
        </div>
        <span className="text-xs text-muted-foreground mt-1">
          {message.timestamp.toLocaleTimeString("fr-FR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
    </div>
  );
}

function formatMessage(content: string): React.ReactNode {
  // Simple markdown-like formatting
  const lines = content.split("\n");

  return lines.map((line, index) => {
    // Bold text
    const formattedLine = line.replace(
      /\*\*(.*?)\*\*/g,
      '<strong class="font-semibold">$1</strong>'
    );

    // Check if line starts with bullet point
    if (line.trim().startsWith("•") || line.trim().startsWith("-")) {
      return (
        <div key={index} className="ml-2">
          {line}
        </div>
      );
    }

    // Check if line is a numbered item
    if (/^\d+\./.test(line.trim())) {
      return (
        <div key={index} className="ml-2">
          {line}
        </div>
      );
    }

    return (
      <span key={index}>
        <span dangerouslySetInnerHTML={{ __html: formattedLine as string }} />
        {index < lines.length - 1 && <br />}
      </span>
    );
  });
}
