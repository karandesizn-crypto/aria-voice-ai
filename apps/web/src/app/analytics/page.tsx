import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

async function fetchAnalytics(token: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return null;
  const response = await fetch(`${apiUrl}/v1/analytics/summary`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return response.json();
}

export default async function AnalyticsPage() {
  const session = await auth();
  if (!session.userId) redirect("/");
  const token = await session.getToken();
  const data = token ? await fetchAnalytics(token) : null;

  return (
    <section className="talk-page">
      <div className="talk-copy">
        <h1>Analytics</h1>
        <p>Session, memory, and tool usage for the last seven days.</p>
      </div>
      {!data ? (
        <p className="voice-panel__hint">Analytics unavailable. Start the API to load metrics.</p>
      ) : (
        <div className="memory-grid">
          <Metric label="Conversations" value={data.conversations} />
          <Metric label="Memories" value={data.memories} />
          <Metric label="Tool calls" value={data.tool_invocations} />
          <Metric
            label="Tool success"
            value={`${Math.round((data.tool_success_rate || 0) * 100)}%`}
          />
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="voice-panel">
      <h2 className="memory-column__title">{label}</h2>
      <p style={{ margin: 0, fontSize: "2rem", fontFamily: "var(--font-display)" }}>{value}</p>
    </div>
  );
}
