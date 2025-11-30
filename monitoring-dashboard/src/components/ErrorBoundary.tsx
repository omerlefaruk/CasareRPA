import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      const isDev = import.meta.env.DEV;

      return (
        <div style={{
          padding: '40px',
          backgroundColor: '#1a1a1f',
          color: '#ef4444',
          minHeight: '100vh',
          fontFamily: 'monospace',
        }}>
          <h1 style={{ color: '#ef4444', marginBottom: '20px' }}>
            Something went wrong
          </h1>
          {isDev ? (
            // Development: Show full error details for debugging
            <pre style={{
              backgroundColor: '#0f0f12',
              padding: '20px',
              borderRadius: '8px',
              overflow: 'auto',
              fontSize: '14px',
              lineHeight: 1.5,
            }}>
              <strong>Error:</strong> {this.state.error?.message}
              {'\n\n'}
              <strong>Stack:</strong>
              {'\n'}
              {this.state.error?.stack}
              {this.state.errorInfo && (
                <>
                  {'\n\n'}
                  <strong>Component Stack:</strong>
                  {'\n'}
                  {this.state.errorInfo.componentStack}
                </>
              )}
            </pre>
          ) : (
            // Production: Generic message without exposing implementation details
            <p style={{
              backgroundColor: '#0f0f12',
              padding: '20px',
              borderRadius: '8px',
              fontSize: '16px',
              color: '#9ca3af',
            }}>
              An unexpected error occurred. Please refresh the page or contact support if the problem persists.
            </p>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              backgroundColor: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
