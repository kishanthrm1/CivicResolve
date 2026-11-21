/**
 * CivicResolve - Global Client-side Utilities
 */

console.log("CivicResolve platform initialized.");

// Global Toast Manager
window.showGlobalToast = function(message, type = 'info') {
    let container = document.getElementById('global-toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'global-toast-container';
        container.className = 'fixed bottom-5 right-5 z-50 space-y-2 pointer-events-none';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const colorClass = type === 'success' ? 'bg-emerald-600' : (type === 'error' ? 'bg-rose-600' : 'bg-slate-900');
    toast.className = `${colorClass} text-white text-xs font-bold px-4 py-3 rounded-2xl shadow-xl flex items-center gap-2 pointer-events-auto animate-fade-in`;
    
    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3500);
};
