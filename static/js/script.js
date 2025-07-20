// Custom JS for toasts and navigation
window.addEventListener('DOMContentLoaded', () => {
  const toastElList = [].slice.call(document.querySelectorAll('.toast'));
  toastElList.forEach(toastEl => {
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
  });

  const toggle = document.getElementById('theme-toggle');
  if (toggle) {
    const setTheme = theme => {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
    };
    const saved = localStorage.getItem('theme');
    if (saved) setTheme(saved);
    toggle.checked = saved === 'dark';
    toggle.addEventListener('change', () => {
      setTheme(toggle.checked ? 'dark' : 'light');
    });
  }
});

function trackEvent(name, props = {}) {
  fetch('/analytics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, props })
  });
}
