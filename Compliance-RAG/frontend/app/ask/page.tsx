import { ChatPanel } from "@/components/ChatPanel";

export default function AskPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8 space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900">Ask</h1>
        <p className="text-sm leading-6 text-zinc-600">
          Ask a question about ingested regulations. The agent retrieves relevant articles, filters
          weak matches, and returns a grounded answer with citations.
        </p>
      </div>
      <ChatPanel />
    </div>
  );
}
