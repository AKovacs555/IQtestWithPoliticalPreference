import React from 'react';

export default function MobileOnlyWrapper({ children }) {
  const [allowed, setAllowed] = React.useState(true);

  React.useEffect(() => {
    const isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent) && window.innerWidth < 768;
    setAllowed(isMobile);
  }, []);

  if (!allowed) {
    return (
      <div className="p-4 text-center">
        <p className="text-lg">Please open this service on a smartphone.</p>
      </div>
    );
  }

  return children;
}
