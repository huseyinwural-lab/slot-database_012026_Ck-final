import { Link } from 'react-router-dom';

const Landing = () => (
  <div className="min-h-screen flex flex-col" data-testid="landing-page">
    <div className="flex-1 container mx-auto px-6 py-16">
      <div className="max-w-2xl space-y-6">
        <div className="text-xs uppercase tracking-[0.3em] text-white/50" data-testid="landing-tagline">Yeni Nesil Casino</div>
        <h1 className="text-4xl font-bold" data-testid="landing-title">
          1 dakikada başlayın, <span className="text-[var(--app-accent,#19e0c3)]">oyunlara</span> dalın.
        </h1>
        <p className="text-white/70" data-testid="landing-description">
          Kayıt ol, doğrulamanı tamamla ve premium oyun lobisinde saniyeler içinde yerini al.
        </p>
        <div className="flex gap-4">
          <Link
            to="/register"
            className="rounded-full bg-[var(--app-cta,#ff8b2c)] px-6 py-3 text-sm font-semibold text-black"
            data-testid="landing-register-cta"
          >
            Kayıt Ol
          </Link>
          <Link
            to="/login"
            className="rounded-full border border-white/20 px-6 py-3 text-sm text-white"
            data-testid="landing-login-cta"
          >
            Giriş Yap
          </Link>
        </div>
      </div>
    </div>
  </div>
);

export default Landing;
