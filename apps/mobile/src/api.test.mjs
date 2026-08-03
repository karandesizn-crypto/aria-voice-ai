import test from "node:test";
import assert from "node:assert/strict";

async function createVoiceSession({ apiUrl, accessToken }) {
  const response = await fetch(`${apiUrl}/v1/voice/sessions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ agent_name: "voice-agent" }),
  });
  if (!response.ok) {
    throw new Error(`Voice session failed (${response.status})`);
  }
  const payload = await response.json();
  return {
    serverUrl: payload.server_url,
    roomName: payload.room_name,
    participantToken: payload.participant_token,
  };
}

test("mobile voice session mapper shape", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () =>
    ({
      ok: true,
      json: async () => ({
        server_url: "wss://livekit.test",
        room_name: "voice-1",
        participant_token: "tok",
      }),
    });

  const session = await createVoiceSession({
    apiUrl: "http://api.test",
    accessToken: "token",
  });
  assert.equal(session.roomName, "voice-1");
  assert.equal(session.serverUrl, "wss://livekit.test");
  globalThis.fetch = original;
});
