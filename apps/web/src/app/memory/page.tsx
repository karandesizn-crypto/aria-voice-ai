import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

type MemoryItem = { content: string; importance?: number };

async function fetchBundle(token: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) return null;
  const response = await fetch(`${apiUrl}/v1/memory/bundle`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return response.json() as Promise<{
    preferences: MemoryItem[];
    semantic: MemoryItem[];
    episodic: MemoryItem[];
  }>;
}

export default async function MemoryPage() {
  const session = await auth();
  if (!session.userId) {
    redirect("/");
  }
  const token = await session.getToken();
  const bundle = token ? await fetchBundle(token) : null;

  return (
    <section className="talk-page">
      <div className="talk-copy">
        <h1>Memory</h1>
        <p>Structured preferences, facts, and recent episodes stored for Aria.</p>
      </div>
      {!bundle ? (
        <p className="voice-panel__hint">Unable to load memory bundle. Is the API running?</p>
      ) : (
        <div className="memory-grid">
          <MemoryColumn title="Preferences" items={bundle.preferences || []} />
          <MemoryColumn title="Facts" items={bundle.semantic || []} />
          <MemoryColumn title="Episodes" items={bundle.episodic || []} />
        </div>
      )}
    </section>
  );
}

function MemoryColumn({ title, items }: { title: string; items: MemoryItem[] }) {
  return (
    <div className="voice-panel">
      <h2 className="memory-column__title">{title}</h2>
      {items.length === 0 ? (
        <p className="voice-panel__hint">None yet.</p>
      ) : (
        <ul className="memory-list">
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item.content}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
