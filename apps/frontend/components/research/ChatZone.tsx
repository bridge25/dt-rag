"use client";

/**
 * ChatZone Component
 * Ethereal Glass Aesthetic
 *
 * Chat interface for Research Agent interactions.
 * @CODE:FRONTEND-UX-002
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
  const roleLabel = isUser ? "사용자" : isSystem ? "시스템" : "어시스턴트";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start"
      )}
      role="article"
      aria-label={`${roleLabel} 메시지`}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 backdrop-blur-md shadow-sm",
          isUser
            ? "bg-blue-600/80 text-white border border-blue-500/30"
            : isSystem
              ? "bg-white/5 text-white/60 text-sm italic border border-white/5"
              : "bg-white/10 text-white border border-white/10"
        )}
      >
        {message.metadata?.isLoading ? (
          <div className="flex items-center gap-2" aria-live="polite">
            <Loader2 className="h-4 w-4 animate-spin text-blue-400" aria-hidden="true" />
            <span className="text-white/60">생각 중...</span>
          </div>
        ) : (
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
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
      aria-label={`제안: ${suggestion.text}`}
      className={cn(
        "flex items-center gap-2 rounded-full px-4 py-2 text-sm",
        "bg-white/5 hover:bg-white/10 text-white/80 hover:text-white",
        "border border-white/10 hover:border-white/20",
        "transition-all duration-200 backdrop-blur-sm",
        "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:ring-offset-2 focus:ring-offset-transparent"
      )}
    >
      <Sparkles className="h-3 w-3 text-blue-400" aria-hidden="true" />
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
    <div className="flex h-full flex-col" role="region" aria-label="리서치 채팅">
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4 bg-white/5 backdrop-blur-md">
        <h2 className="text-lg font-semibold text-white" id="chat-title">리서치 에이전트</h2>
        <p className="text-sm text-white/60">
          원하는 전문 지식 영역을 설명해 주세요
        </p>
      </header>

      {/* Messages Area */}
      <div
        className="flex-1 overflow-y-auto p-6 custom-scrollbar"
        role="log"
        aria-label="메시지 목록"
        aria-live="polite"
        aria-relevant="additions"
      >
        {showSuggestions ? (
          <div className="flex h-full flex-col items-center justify-center gap-8">
            <div className="text-center">
              <div className="mx-auto h-16 w-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center mb-6 border border-white/10 shadow-glass">
                <Sparkles className="h-8 w-8 text-blue-400" />
              </div>
              <h3 className="text-xl font-medium text-white mb-2">무엇을 리서치할까요?</h3>
              <p className="text-white/60 max-w-xs mx-auto">
                원하는 지식 영역을 자연어로 설명해 주세요
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-3 max-w-md">
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
          <div className="space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <footer className="border-t border-white/10 p-4 bg-white/5 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-end gap-3"
          role="form"
          aria-label="메시지 입력"
        >
          <label htmlFor="research-input" className="sr-only">
            리서치 주제 입력
          </label>
          <Textarea
            id="research-input"
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="리서치하고 싶은 주제를 입력하세요..."
            disabled={disabled || isLoading}
            rows={1}
            className="min-h-[44px] max-h-[120px] resize-none bg-white/5 border-white/10 text-white placeholder:text-white/30 focus:ring-blue-500/50 focus:border-blue-500/50 rounded-xl"
            aria-describedby="input-hint"
          />
          <span id="input-hint" className="sr-only">
            Enter로 전송, Shift+Enter로 줄바꿈
          </span>
          <Button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            size="icon"
            className={cn(
              "h-11 w-11 shrink-0 rounded-xl transition-all",
              !input.trim() || isLoading || disabled
                ? "bg-white/5 text-white/20"
                : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20"
            )}
            aria-label={isLoading ? "전송 중" : "메시지 전송"}
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            ) : (
              <Send className="h-5 w-5" aria-hidden="true" />
            )}
          </Button>
        </form>
      </footer>
    </div>
  );
}

export default ChatZone;
