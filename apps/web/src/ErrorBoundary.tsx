import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div className="flex min-h-screen min-w-0 items-center justify-center bg-gray-100 p-4 sm:p-8">
          <div className="min-w-0 w-full max-w-lg rounded-lg border border-red-200 bg-white p-4 sm:p-6 shadow">
            <h1 className="mb-2 text-lg font-semibold text-red-700">Fehler</h1>
            <p className="mb-4 text-sm text-gray-600">{this.state.error.message}</p>
            <pre className="mb-4 max-w-full overflow-auto break-words rounded bg-gray-100 p-3 text-xs">
              {this.state.error.stack}
            </pre>
            <button
              type="button"
              className="min-h-touch min-w-touch rounded bg-primary-500 px-4 py-2 text-white hover:bg-primary-600"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Erneut versuchen
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
