export async function createVoiceSession({
  apiUrl,
  accessToken,
}: {
  apiUrl: string;
  accessToken: string;
}) {
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
