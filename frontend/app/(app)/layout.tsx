import TopNav from "@/components/layout/TopNav";
import { PersonalSidebar } from "@/components/layout/PersonalSidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <TopNav />
      <div className="flex flex-1">
        <PersonalSidebar />
        <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-8">
          {children}
        </main>
      </div>
    </div>
  );
}
