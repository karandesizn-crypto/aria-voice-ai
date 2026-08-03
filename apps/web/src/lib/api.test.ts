import { describe, expect, it, vi } from "vitest";
import { createVoiceSession } from "@/lib/api";

describe("createVoiceSession", () => {
  it("maps API payload into camelCase client model", async () => {
    process.env.NEXT_PUBLIC_API_URL = "http://api.test";

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        server_url: "wss://livekit.test",
        room_name: "voice-user-1",
        participant_identity: "user_1",
        participant_token: "jwt.token.value",
        expires_in_seconds: 3600,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const session = await createVoiceSession("clerk-token", { language: "hi" });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/v1/voice/sessions",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer clerk-token",
        }),
        body: JSON.stringify({ agent_name: "voice-agent", language: "hi" }),
      }),
    );
    expect(session).toEqual({
      serverUrl: "wss://livekit.test",
      roomName: "voice-user-1",
      participantIdentity: "user_1",
      participantToken: "jwt.token.value",
      expiresInSeconds: 3600,
    });
  });
});
