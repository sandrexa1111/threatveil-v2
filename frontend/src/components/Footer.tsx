export function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 pt-6 text-sm text-slate-500">
      <p>© {new Date().getFullYear()} ThreatVeilAI. Passive recon only.</p>
      <p className="mt-1">Backend: FastAPI on Render/Railway • Frontend: Next.js on Vercel</p>
    </footer>
  );
}
