"use client";

import { FormEvent, useMemo, useState } from "react";

type Citation = {
  title: string;
  url: string;
  snippet: string;
};

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
};

type AskResponse = {
  answer: string;
  citations?: Citation[];
};

function getErrorMessage(status: number): string {
  if (status === 404) {
    return "Ask endpoint not found. Verify API base URL configuration.";
  }
  if (status === 429) {
    return "Rate limited. Please wait and try again.";
  }
  if (status >= 500) {
    return "Backend service error. Please try again in a moment.";
  }
  return "Request failed. Please try again.";
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export default function AskSuperFriendPage() {
  const [question, setQuestion] = useState("");
  const [lastQuestion, setLastQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim().replace(/\/$/, ""),
    [],
  );
  const chatEnabled = Boolean(apiBaseUrl);

  async function submitQuestion(rawQuestion: string) {
    const trimmed = rawQuestion.trim();
    if (!trimmed || isLoading || !chatEnabled) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setLastQuestion(trimmed);
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetchWithTimeout(
        `${apiBaseUrl}/ask`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: trimmed }),
        },
        25000,
      );

      if (!response.ok) {
        throw new Error(getErrorMessage(response.status));
      }

      const payload = (await response.json()) as Partial<AskResponse>;
      const text = typeof payload.answer === "string" ? payload.answer.trim() : "";
      if (!text) {
        throw new Error("No answer returned from backend.");
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        text,
        citations: Array.isArray(payload.citations) ? payload.citations : [],
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        setError("Request timed out. Please try again.");
      } else {
        const message = err instanceof Error ? err.message : "Chat mode currently unavailable.";
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuestion(question);
  }

  async function retryLastQuestion() {
    if (!lastQuestion || isLoading) {
      return;
    }
    await submitQuestion(lastQuestion);
  }

  return (
    <section className="space-y-4 sm:space-y-5">
      <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
        <p className="text-sm text-slate-800">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="mr-2 inline-block h-5 w-5 align-text-bottom text-msc-navy"
            aria-hidden="true"
          >
            <rect x="4" y="5" width="16" height="12" rx="2" />
            <path d="M9 21h6M12 17v4M9 10h.01M15 10h.01M9 13c.8.7 1.8 1 3 1s2.2-.3 3-1" />
          </svg>
          Ask a question and I&apos;ll help you find guidance, summarize sources, and point you to relevant publications.
        </p>
      </div>

      {!chatEnabled ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Chat mode is unavailable. Configure <code>NEXT_PUBLIC_API_BASE_URL</code> to enable Ask.
        </div>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
        <label htmlFor="ask-input" className="block text-sm font-medium text-slate-900">
          Ask a question
        </label>
        <textarea
          id="ask-input"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="What is an MSC?"
          rows={4}
          disabled={isLoading || !chatEnabled}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-black placeholder:text-slate-500 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200 disabled:cursor-not-allowed disabled:bg-slate-100"
        />
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={isLoading || !chatEnabled}
            className="inline-flex items-center justify-center rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 active:bg-slate-950 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            {isLoading ? "Getting Answer..." : "Get Answer"}
          </button>
          <button
            type="button"
            onClick={retryLastQuestion}
            disabled={isLoading || !lastQuestion || !chatEnabled}
            className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:text-slate-400"
          >
            Retry Last
          </button>
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
      </form>

      <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
        <h3 className="text-sm font-semibold text-slate-900">Chat Transcript</h3>
        {messages.length === 0 ? (
          <p className="text-sm text-slate-500">No messages yet. Submit a question to start the transcript.</p>
        ) : (
          <ul className="space-y-2">
            {messages.map((message) => (
              <li
                key={message.id}
                className={`rounded-lg p-3 text-sm ${
                  message.role === "user" ? "bg-slate-100 text-slate-900" : "bg-[#f8eef1] text-slate-900"
                }`}
              >
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-600">
                  {message.role === "assistant" ? "Super Friend" : "User"}
                </p>
                <p>{message.text}</p>
                {message.role === "assistant" && message.citations && message.citations.length > 0 ? (
                  <div className="mt-3">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-600">Citations</p>
                    <ul className="space-y-1">
                      {message.citations.map((citation, index) => (
                        <li key={`${message.id}-citation-${index}`}>
                          {citation.url ? (
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-slate-800 underline underline-offset-2 hover:text-slate-900"
                            >
                              {citation.title || `Citation ${index + 1}`}
                            </a>
                          ) : (
                            <span className="text-sm text-slate-800">{citation.title || `Citation ${index + 1}`}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
