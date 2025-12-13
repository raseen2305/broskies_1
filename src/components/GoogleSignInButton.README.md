# GoogleSignInButton Component

A reusable button component for Google OAuth authentication that follows Google's official branding guidelines.

## Features

- ✅ Official Google logo with correct brand colors (Blue #4285F4, Red #EA4335, Yellow #FBBC05, Green #34A853)
- ✅ Loading state with animated spinner
- ✅ Disabled state handling
- ✅ Smooth hover and tap animations via Framer Motion
- ✅ Keyboard accessible with focus ring
- ✅ Responsive design
- ✅ TypeScript support

## Usage

```tsx
import GoogleSignInButton from '../components/GoogleSignInButton';

function AuthPage() {
  const [isLoading, setIsLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      // Your OAuth logic here
      const authUrl = await getGoogleAuthUrl();
      window.location.href = authUrl;
    } catch (error) {
      console.error('Sign in failed:', error);
      setIsLoading(false);
    }
  };

  return (
    <GoogleSignInButton 
      onClick={handleGoogleSignIn}
      loading={isLoading}
      disabled={false}
    />
  );
}
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onClick` | `() => void` | Required | Callback function when button is clicked |
| `loading` | `boolean` | `false` | Shows loading spinner and disables button |
| `disabled` | `boolean` | `false` | Disables the button |
| `className` | `string` | `''` | Additional CSS classes to apply |

## Design Guidelines

This component follows [Google's Sign-In Branding Guidelines](https://developers.google.com/identity/branding-guidelines):

- Uses the official Google "G" logo
- Maintains proper color scheme
- Includes appropriate padding and sizing
- Shows clear loading and disabled states
- Provides accessible focus indicators

## States

### Default State
- White background with gray border
- Google logo on the left
- "Continue with Google" text centered
- Subtle shadow on hover

### Loading State
- Animated spinner replaces Google logo
- Text changes to "Signing in..."
- Button is disabled during loading
- Cursor shows not-allowed

### Disabled State
- Reduced opacity (50%)
- No hover effects
- Cursor shows not-allowed

## Accessibility

- Semantic `<button>` element
- Keyboard focusable with visible focus ring
- Disabled state properly communicated to screen readers
- Sufficient color contrast for text

## Dependencies

- `react` - Core React library
- `framer-motion` - Animation library for smooth interactions

## Related Components

- `HRAuth` - Uses this button for HR authentication
- `AnimatedButton` - General purpose animated button component
