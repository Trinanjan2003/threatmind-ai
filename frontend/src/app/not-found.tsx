import Link from "next/link";
import { ShieldHalf } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-sky-500 shadow-lg shadow-primary/30">
        <ShieldHalf className="size-7 text-white" />
      </div>
      <div>
        <p className="text-5xl font-semibold tracking-tight">404</p>
        <p className="mt-2 text-muted-foreground">This page could not be found.</p>
      </div>
      <Link
        href="/dashboard"
        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Back to dashboard
      </Link>
    </div>
  );
}
