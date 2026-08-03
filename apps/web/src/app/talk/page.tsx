import { VoiceSessionPanel } from "@/components/voice-session-panel";

export default function TalkPage() {
  return (
    <section className="talk-stage relative flex min-h-[calc(100vh-5rem)] flex-1 flex-col items-center justify-center overflow-hidden bg-black px-8 py-10">
      <div className="relative z-10 w-full max-w-3xl">
        <VoiceSessionPanel />
      </div>
    </section>
  );
}
