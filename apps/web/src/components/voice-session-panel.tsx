"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  useConnectionState,
  useLocalParticipant,
  useVoiceAssistant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { useAuth } from "@clerk/nextjs";
import { Mic, MicOff, PhoneOff } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { VoicePoweredOrb } from "@/components/ui/voice-powered-orb";
import { createVoiceSession, type VoiceSession } from "@/lib/api";
import {
  DEFAULT_VOICE_LANGUAGE,
  VOICE_LANGUAGES,
} from "@/lib/languages";
import { cn } from "@/lib/utils";

type SessionStatus = "idle" | "connecting" | "live" | "error";

export function VoiceSessionPanel() {
  const { getToken, isSignedIn } = useAuth();
  const [session, setSession] = useState<VoiceSession | null>(null);
  const [status, setStatus] = useState<SessionStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState(DEFAULT_VOICE_LANGUAGE);

  const startSession = useCallback(async () => {
    if (!isSignedIn) {
      setError("Sign in to start a voice session.");
      return;
    }

    setStatus("connecting");
    setError(null);

    try {
      const token = await getToken();
      if (!token) {
        throw new Error("Unable to obtain Clerk session token");
      }
      const next = await createVoiceSession(token, { language });
      setSession(next);
      setStatus("live");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setStatus("error");
      setSession(null);
    }
  }, [getToken, isSignedIn, language]);

  const endSession = useCallback(() => {
    setSession(null);
    setStatus("idle");
    setError(null);
  }, []);

  const selectedLabel =
    VOICE_LANGUAGES.find((item) => item.code === language)?.label ?? "English";

  if (!session) {
    return (
      <div className="flex flex-col items-center space-y-8">
        <div className="relative h-80 w-80 sm:h-96 sm:w-96">
          <VoicePoweredOrb
            hue={0}
            enableVoiceControl={false}
            className="overflow-hidden rounded-xl"
          />
        </div>

        <label className="grid w-full max-w-md gap-2 text-left">
          <span className="text-sm text-neutral-400">Language</span>
          <div className="relative">
            <select
              className="h-11 w-full appearance-none rounded-md border border-neutral-700 bg-neutral-950 py-2 pl-3 pr-9 text-sm text-neutral-100 outline-none focus-visible:ring-2 focus-visible:ring-neutral-500"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              disabled={status === "connecting"}
              aria-label="Conversation language"
            >
              {VOICE_LANGUAGES.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </select>
            <span
              aria-hidden
              className="pointer-events-none absolute inset-y-0 right-2.5 flex items-center text-neutral-300"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="m6 9 6 6 6-6" />
              </svg>
            </span>
          </div>
        </label>

        <Button
          size="lg"
          className="px-8 py-3"
          onClick={startSession}
          disabled={status === "connecting"}
        >
          {status === "connecting" ? (
            "Connecting…"
          ) : (
            <>
              <Mic className="mr-3 h-5 w-5" />
              Start talking
            </>
          )}
        </Button>

        <p className="max-w-md text-center text-muted-foreground">
          Choose a language, then start talking. Speak freely — the agent yields when
          you interrupt.
        </p>

        {error ? (
          <p className="text-sm text-red-400" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={session.participantToken}
      serverUrl={session.serverUrl}
      connect
      audio
      video={false}
      onDisconnected={endSession}
      className="w-full"
    >
      <RoomAudioRenderer />
      <VoiceRoomControls
        roomName={session.roomName}
        languageLabel={selectedLabel}
        onEnd={endSession}
      />
    </LiveKitRoom>
  );
}

function VoiceRoomControls({
  roomName,
  languageLabel,
  onEnd,
}: {
  roomName: string;
  languageLabel: string;
  onEnd: () => void;
}) {
  const connectionState = useConnectionState();
  const { localParticipant } = useLocalParticipant();
  const { state: agentState } = useVoiceAssistant();
  const [micEnabled, setMicEnabled] = useState(true);

  useEffect(() => {
    void localParticipant.setMicrophoneEnabled(micEnabled);
  }, [localParticipant, micEnabled]);

  const label =
    connectionState === ConnectionState.Connected
      ? agentState === "speaking"
        ? "Agent speaking"
        : agentState === "listening"
          ? "Listening"
          : agentState === "thinking"
            ? "Thinking"
            : "Connected"
      : String(connectionState);

  return (
    <div className="flex flex-col items-center space-y-8">
      <div
        className={cn(
          "relative h-80 w-80 transition-transform duration-500 sm:h-96 sm:w-96",
          agentState === "speaking" && "scale-[1.02]",
        )}
      >
        {/* Exact prompt orb colors (hue=0). LiveKit owns the mic, so voice-control stays off. */}
        <VoicePoweredOrb
          hue={0}
          enableVoiceControl={false}
          maxHoverIntensity={agentState === "speaking" ? 0.9 : 0.55}
          className="overflow-hidden rounded-xl"
        />
      </div>

      <div className="space-y-1 text-center">
        <p className="text-lg font-medium text-neutral-100">{label}</p>
        <p className="text-sm text-muted-foreground">
          {languageLabel} · Room {roomName}
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button
          type="button"
          variant={micEnabled ? "default" : "outline"}
          size="lg"
          className="px-8 py-3"
          onClick={() => setMicEnabled((value) => !value)}
        >
          {micEnabled ? (
            <>
              <Mic className="mr-3 h-5 w-5" />
              Mute
            </>
          ) : (
            <>
              <MicOff className="mr-3 h-5 w-5" />
              Unmute
            </>
          )}
        </Button>
        <Button
          type="button"
          variant="destructive"
          size="lg"
          className="px-8 py-3"
          onClick={onEnd}
        >
          <PhoneOff className="mr-3 h-5 w-5" />
          End
        </Button>
      </div>
    </div>
  );
}
