import { useEffect, useState } from 'react';

const THEME_KEY = 'player_theme_settings';

const defaultTheme = {
  background: '#05080f',
  header: '#0d111a',
  footer: '#0b0f18',
  menu: '#0d111a',
};

const applyTheme = (theme) => {
  const root = document.documentElement;
  root.style.setProperty('--player-bg', theme.background);
  root.style.setProperty('--player-header', theme.header);
  root.style.setProperty('--player-footer', theme.footer);
  root.style.setProperty('--player-menu', theme.menu);
};

export const ThemeCustomizer = () => {
  const [theme, setTheme] = useState(defaultTheme);

  useEffect(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      setTheme(parsed);
      applyTheme(parsed);
    } else {
      applyTheme(defaultTheme);
    }
  }, []);

  const handleChange = (key, value) => {
    const next = { ...theme, [key]: value };
    setTheme(next);
    localStorage.setItem(THEME_KEY, JSON.stringify(next));
    applyTheme(next);
  };

  return (
    <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3" data-testid="theme-customizer">
      <div className="text-sm font-semibold">Tema Ayarları</div>
      <div className="grid gap-3 md:grid-cols-2">
        {['background', 'header', 'footer', 'menu'].map((key) => (
          <label key={key} className="flex items-center justify-between text-sm" data-testid={`theme-${key}-setting`}>
            <span className="capitalize">{key}</span>
            <input
              type="color"
              value={theme[key]}
              onChange={(event) => handleChange(key, event.target.value)}
              className="h-8 w-12 rounded border border-white/20 bg-transparent"
              data-testid={`theme-${key}-input`}
            />
          </label>
        ))}
      </div>
    </div>
  );
};
