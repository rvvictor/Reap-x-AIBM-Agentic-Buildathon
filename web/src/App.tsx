import type { ComponentType } from "react";

// Each feature is web/src/features/<name>/index.tsx with `export default` and `order`.
// Adding a feature = creating its folder; App.tsx never becomes a conflict point.
type FeatureModule = { default: ComponentType; order?: number };

const features = Object.entries(
  import.meta.glob<FeatureModule>("./features/*/index.tsx", { eager: true }),
)
  .map(([path, module]) => ({ path, ...module }))
  .sort((a, b) => (a.order ?? 100) - (b.order ?? 100));

export default function App() {
  return (
    <main className="mx-auto min-h-[100dvh] max-w-7xl px-4 py-12 font-sans text-zinc-900 dark:text-zinc-100">
      {features.map(({ path, default: Feature }) => (
        <Feature key={path} />
      ))}
    </main>
  );
}
