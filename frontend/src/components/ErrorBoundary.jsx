import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle, RefreshCw, LogOut } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch() {
    // Intentionally do not log to console in production UI polish phase.
  }

  handleLogout = () => {
    try {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_user');
      localStorage.removeItem('impersonate_tenant_id');
    } catch {
      // ignore
    }

    window.location.href = '/login';
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-slate-50">
          <Card className="w-full max-w-md shadow-lg border-red-200">
            <CardHeader className="text-center">
              <div className="mx-auto bg-red-100 p-3 rounded-full w-fit mb-4">
                <AlertTriangle className="w-8 h-8 text-red-600" />
              </div>
              <CardTitle className="text-xl">Bir şeyler ters gitti</CardTitle>
              <CardDescription>
                Beklenmedik bir hata oluştu. Yenilemeyi deneyebilir veya temiz bir başlangıç için çıkış yapabilirsiniz.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <div className="flex gap-2">
                <Button onClick={this.handleReload} className="w-full" variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" /> Yenile
                </Button>
                <Button onClick={this.handleLogout} className="w-full" variant="destructive">
                  <LogOut className="w-4 h-4 mr-2" /> Çıkış Yap
                </Button>
              </div>
              <div className="bg-slate-100 p-3 rounded text-xs font-mono text-left overflow-auto max-h-32">
                {this.state.error?.message || 'Unknown Error'}
              </div>
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
