import { BiodiversityExplorer } from "@/features/explorer/components/biodiversity-explorer";

export default function Home() {
  return (
    <main className="min-h-screen bg-background p-6">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header>
          <h1 className="text-2xl font-semibold">
            Biodiversity explorer
          </h1>
          <p className="text-muted-foreground">
            Explore observations by species and region.
          </p>
        </header>

        <BiodiversityExplorer />
      </div>
    </main>
  );
}
