export type VoiceSession = {
  serverUrl: string;
  roomName: string;
  participantIdentity: string;
  participantToken: string;
  expiresInSeconds: number;
};

type ApiVoiceSession = {
  server_url: string;
  room_name: string;
  participant_identity: string;
  participant_token: string;
  expires_in_seconds: number;
};

export type CreateVoiceSessionOptions = {
  language?: string;
  agentName?: string;
};

export async function createVoiceSession(
  accessToken: string,
  options: CreateVoiceSessionOptions = {},
): Promise<VoiceSession> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured");
  }

  const response = await fetch(`${apiUrl}/v1/voice/sessions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      agent_name: options.agentName ?? "voice-agent",
      language: options.language ?? "en",
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Failed to create voice session (${response.status}): ${detail}`);
  }

  const payload = (await response.json()) as ApiVoiceSession;
  return {
    serverUrl: payload.server_url,
    roomName: payload.room_name,
    participantIdentity: payload.participant_identity,
    participantToken: payload.participant_token,
    expiresInSeconds: payload.expires_in_seconds,
  };
}
