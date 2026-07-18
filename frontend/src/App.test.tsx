import { render, screen } from '@testing-library/react';
import App from './App';

test('renders onboarding screen', () => {
  render(<App />);
  const skipButton = screen.getByText(/pular/i);
  expect(skipButton).toBeInTheDocument();
});
