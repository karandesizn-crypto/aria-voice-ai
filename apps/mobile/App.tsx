import { StatusBar } from "expo-status-bar";
import { useState } from "react";
import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { createVoiceSession } from "./src/api";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export default function App() {
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState<string | null>(null);

  async function onStart() {
    setStatus("Connecting…");
    setError(null);
    try {
      // Mobile obtains a Clerk token via expo auth session in production.
      // Phase 4 ships the API client + talk CTA against the shared control plane.
      const session = await createVoiceSession({
        apiUrl: API_URL,
        accessToken: process.env.EXPO_PUBLIC_DEV_TOKEN ?? "",
      });
      setStatus(`Joined ${session.roomName}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start");
      setStatus("Error");
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.brand}>Aria</Text>
        <Text style={styles.lede}>Mobile voice session for your persistent agent.</Text>
        <Pressable style={styles.button} onPress={onStart}>
          <Text style={styles.buttonText}>Start talking</Text>
        </Pressable>
        <Text style={styles.status}>{status}</Text>
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <StatusBar style="dark" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f7f3ec" },
  container: { flex: 1, padding: 24, justifyContent: "center", gap: 12 },
  brand: { fontSize: 48, fontWeight: "700", color: "#1c1917" },
  lede: { fontSize: 16, color: "#44403c", maxWidth: 320 },
  button: {
    alignSelf: "flex-start",
    backgroundColor: "#0f766e",
    paddingHorizontal: 18,
    paddingVertical: 12,
    borderRadius: 999,
  },
  buttonText: { color: "white", fontWeight: "700" },
  status: { color: "#44403c" },
  error: { color: "#b91c1c" },
});
