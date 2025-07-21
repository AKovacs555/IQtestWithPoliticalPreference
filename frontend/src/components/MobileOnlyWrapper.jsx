import React from 'react';

// Component gatekeeping the application to smartphones only. It checks both the
// user agent and viewport width. If the device does not appear to be a phone the
// app is replaced with an explanatory message.
export default function MobileOnlyWrapper({ children }) {
  // Previously restricted to mobile devices. The new responsive design works across viewports.
  return children;
}
