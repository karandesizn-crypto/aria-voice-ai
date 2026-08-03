import { Show, SignInButton, UserButton } from "@clerk/nextjs";
import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand">
        Aria
      </Link>
      <nav className="site-nav">
        <Show when="signed-out">
          <SignInButton mode="modal">
            <button type="button" className="btn btn-secondary">
              Sign in
            </button>
          </SignInButton>
        </Show>
        <Show when="signed-in">
          <Link href="/talk" className="nav-link">
            Talk
          </Link>
          <Link href="/memory" className="nav-link">
            Memory
          </Link>
          <Link href="/analytics" className="nav-link">
            Analytics
          </Link>
          <UserButton />
        </Show>
      </nav>
    </header>
  );
}
