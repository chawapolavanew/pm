"use client";

import { useEffect, useRef, useState } from "react";
import { apiChat } from "@/lib/api";
import { getToken } from "@/lib/auth";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  onBoardUpdated: () => void;
};

export const ChatSidebar = ({ onBoardUpdated }: Props) => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const token = getToken() ?? "";

  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView?.({ behavior: "smooth" });
      inputRef.current?.focus();
    }
  }, [open, messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await apiChat(token, text, history);
      setMessages([...next, { role: "assistant", content: res.reply }]);
      if (res.board_updated) onBoardUpdated();
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close AI chat" : "Open AI chat"}
        className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[var(--secondary-purple)] shadow-[0_8px_24px_rgba(117,57,145,0.4)] transition-transform hover:scale-105 active:scale-95"
      >
        {open ? (
          <CloseIcon />
        ) : (
          <ChatIcon />
        )}
      </button>

      {/* Sidebar panel */}
      <div
        data-testid="chat-sidebar"
        className={`fixed bottom-0 right-0 z-30 flex h-full max-h-screen w-full flex-col border-l border-[var(--stroke)] bg-white shadow-[-8px_0_40px_rgba(3,33,71,0.1)] transition-transform duration-300 sm:w-[420px] ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
              AI Assistant
            </p>
            <h2 className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
              Board Chat
            </h2>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close AI chat"
            className="rounded-xl border border-[var(--stroke)] p-2 text-[var(--gray-text)] transition hover:border-[var(--navy-dark)] hover:text-[var(--navy-dark)]"
          >
            <CloseIcon />
          </button>
        </div>

        {/* Message list */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {messages.length === 0 && (
            <div className="mt-8 text-center">
              <p className="text-sm font-semibold text-[var(--navy-dark)]">
                Ask me anything about your board.
              </p>
              <p className="mt-2 text-xs text-[var(--gray-text)]">
                I can create, move, update, or delete cards for you.
              </p>
              <div className="mt-6 flex flex-col gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => { setInput(s); inputRef.current?.focus(); }}
                    className="rounded-xl border border-[var(--stroke)] px-4 py-2.5 text-left text-xs text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col gap-3">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                    msg.role === "user"
                      ? "bg-[var(--secondary-purple)] text-white"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--navy-dark)]"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3">
                  <ThinkingDots />
                </div>
              </div>
            )}
          </div>

          {error && (
            <p className="mt-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-600">
              {error}
            </p>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="border-t border-[var(--stroke)] p-4">
          <div className="flex items-end gap-3 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 focus-within:border-[var(--primary-blue)] focus-within:ring-2 focus-within:ring-[var(--primary-blue)]/20">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask the AI..."
              disabled={loading}
              className="flex-1 resize-none bg-transparent text-sm text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)] disabled:opacity-50"
              style={{ maxHeight: "120px" }}
            />
            <button
              onClick={send}
              disabled={!input.trim() || loading}
              aria-label="Send message"
              className="flex-shrink-0 rounded-xl bg-[var(--secondary-purple)] p-2 text-white transition-opacity hover:opacity-90 disabled:opacity-40"
            >
              <SendIcon />
            </button>
          </div>
          <p className="mt-2 text-center text-xs text-[var(--gray-text)]">
            Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Backdrop on mobile */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/20 sm:hidden"
          onClick={() => setOpen(false)}
        />
      )}
    </>
  );
};

const SUGGESTIONS = [
  "Add a card called 'Write tests' to Backlog",
  "Move all Done cards to Review",
  "What cards are in progress?",
];

function ChatIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-[var(--gray-text)]"
          style={{ animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }}
        />
      ))}
    </div>
  );
}
