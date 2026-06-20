import LiveMap from "../components/LiveMap";
import Settings from "../components/Settings";

export default function DashboardPage(): JSX.Element {
  return (
    <div className="fixed inset-0 overflow-hidden bg-slate-100 dark:bg-slate-950">
      {/* Background Map layer */}
      <div className="absolute inset-0 z-0">
        <LiveMap />
      </div>

      {/* Floating Settings Panel Layer */}
      <div className="pointer-events-none absolute inset-0 z-10 flex p-6 md:p-8 pt-[100px]">
        <div className="pointer-events-auto w-[340px] shrink-0">
          <Settings />
        </div>
      </div>
    </div>
  );
}
