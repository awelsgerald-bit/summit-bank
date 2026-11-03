import { Component } from 'react';

// If a screen crashes, show a message and a way back instead of a blank page.
export default class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error) {
    console.error('Screen crashed:', error);
  }

  componentDidUpdate(prev) {
    if (this.state.error && prev.resetKey !== this.props.resetKey) this.setState({ error: null });
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="max-w-lg mx-auto glass rounded-3xl p-8 text-center space-y-4" role="alert">
        <h2 className="font-display text-lg font-medium">Something went wrong on this screen</h2>
        <p className="text-sm text-[var(--text-3)] break-words">{String(this.state.error?.message || this.state.error)}</p>
        <button onClick={() => window.location.assign('/dashboard')} className="btn-primary rounded-full px-6 py-2.5 text-sm font-medium">
          Back to dashboard
        </button>
      </div>
    );
  }
}
