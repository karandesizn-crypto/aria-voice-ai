import { Show, SignInButton } from "@clerk/nextjs";
import Link from "next/link";

export default function HomePage() {
  return (
    <section className="hero">
      <div className="hero-atmosphere" aria-hidden />
      <div className="hero-copy">
        <p className="brand-mark">Aria</p>
        <h1>Talk with an agent that stays with you.</h1>
        <p className="hero-lede">
          Realtime voice, natural interruptions, and a platform built for long-term memory and tools.
        </p>
        <div className="hero-actions">
          <Show
            when="signed-out"
            fallback={
              <Link href="/talk" className="btn btn-primary">
                Open voice room
              </Link>
            }
          >
            <SignInButton mode="modal">
              <button type="button" className="btn btn-primary">
                Get started
              </button>
            </SignInButton>
          </Show>
        </div>
      </div>
    </section>
  );
}
