export const CategoryRail = ({ title, items }) => (
  <div className="space-y-3" data-testid={`category-rail-${title.toLowerCase()}`}>
    <div className="text-sm font-semibold text-white/90" data-testid={`category-rail-${title}-title`}>{title}</div>
    <div className="grid gap-3 md:grid-cols-4">
      {items}
    </div>
  </div>
);
