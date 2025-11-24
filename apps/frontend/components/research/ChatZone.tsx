"use client";

/**
 * ChatZone Component
 *
 * Chat interface for Research Agent interactions.
 * @CODE:FRONTEND-UX-001
 */

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { ChatMessage, ChatSuggestion } from "@/types/research";

// ============================================================================
// Props
// ============================================================================

interface ChatZoneProps {
  messages: ChatMessage[];
  onSendMessage: (content: string) => void;
  suggestions?: ChatSuggestion[];
  isLoading?: boolean;
  disabled?: boolean;
}

// ============================================================================
// Default Suggestions
// ============================================================================

const DEFAULT_SUGGESTIONS: ChatSuggestion[] = [
  {
    id: "1",
    text: "암 전문 의학박사 에이전트 만들고 싶어",
    category: "example",
  },
  {
    id: "2",
    text: "최신 AI 기술 트렌드 리서치",
    category: "example",
  },
  {
    id: "3",
    text: "스타트업 투자 전략 자료 수집",
    category: "example",
  },
];

// ============================================================================
// Message Bubble Component
// ============================================================================

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary text-primary-foreground"
            : isSystem
            ? "bg-muted text-muted-foreground text-sm italic"
            : "bg-secondary text-secondary-foreground"
        )}
      >
        {message.metadata?.isLoading ? (
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>생각 중...</span>
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{message.content}</p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Suggestion Chip Component
// ============================================================================

function SuggestionChip({
  suggestion,
  onClick,
}: {
  suggestion: ChatSuggestion;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 rounded-full px-4 py-2 text-sm",
        "bg-secondary/50 hover:bg-secondary",
        "border border-border/50 hover:border-border",
        "transition-colors duration-200"
      )}
    >
      <Sparkles className="h-3 w-3 text-primary" />
      <span className="truncate">{suggestion.text}</span>
    </button>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function ChatZone({
  messages,
  onSendMessage,
  suggestions = DEFAULT_SUGGESTIONS,
  isLoading = false,
  disabled = false,
}: ChatZoneProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || isLoading || disabled) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (text: string) => {
    setInput(text);
    textareaRef.current?.focus();
  };

  const showSuggestions = messages.length === 0 && !isLoading;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b px-4 py-3">
        <h2 className="text-lg font-semibold">리서치 에이전트</h2>
        <p className="text-sm text-muted-foreground">
          원하는 전문 지식 영역을 설명해 주세요
        </p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {showSuggestions ? (
          <div className="flex h-full flex-col items-center justify-center gap-6">
            <div className="text-center">
              <Sparkles className="mx-auto h-12 w-12 text-primary/50" />
              <h3 className="mt-4 text-lg font-medium">무엇을 리서치할까요?</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                원하는 지식 영역을 자연어로 설명해 주세요
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((suggestion) => (
                <SuggestionChip
                  key={suggestion.id}
                  suggestion={suggestion}
                  onClick={() => handleSuggestionClick(suggestion.text)}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex items-end gap-2">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="리서치하고 싶은 주제를 입력하세요..."
            disabled={disabled || isLoading}
            rows={1}
            className="min-h-[44px] max-h-[120px] resize-none"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isLoading || disabled}
            size="icon"
            className="h-11 w-11 shrink-0"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default ChatZone;
