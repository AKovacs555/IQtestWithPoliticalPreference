// Custom JS for toasts and navigation
window.addEventListener('DOMContentLoaded', () => {
  const toastElList = [].slice.call(document.querySelectorAll('.toast'));
  toastElList.forEach(toastEl => {
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
  });
});
