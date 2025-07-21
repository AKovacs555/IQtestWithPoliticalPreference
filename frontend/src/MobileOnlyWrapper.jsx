import React from 'react';

// Component gatekeeping the application to smartphones only. It checks both the
// user agent and viewport width. If the device does not appear to be a phone the
// app is replaced with an explanatory message.
export default function MobileOnlyWrapper({ children }) {
  const [allowed, setAllowed] = React.useState(true);

  React.useEffect(() => {
    const isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent) && window.innerWidth < 768;
    setAllowed(isMobile);
  }, []);

  if (!allowed) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4 text-center space-y-2">
        <h1 className="text-2xl font-bold">Mobile Device Required</h1>
        <p>This quiz is optimised for phones. Please visit again on your smartphone.</p>
      </div>
    );
  }

  return children;
}
