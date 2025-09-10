(function () {
  'use strict';

  // Initialize popovers for the help icons. Try Bootstrap first; if not available, use a lightweight fallback.
  document.addEventListener('DOMContentLoaded', function () {
    var triggers = Array.prototype.slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    if (window.bootstrap && bootstrap.Popover) {
      triggers.forEach(function (el) {
        try {
          new bootstrap.Popover(el, {html: true, placement: 'right'});
        } catch (e) {
          // ignore
        }
      });
      return;
    }

    // Inject minimal CSS for custom popovers
    if (!document.getElementById('custom-popover-styles')) {
      var style = document.createElement('style');
      style.id = 'custom-popover-styles';
      style.textContent = '\n.custom-popover {\n  position: absolute;\n  z-index: 1060;\n  background: #fff;\n  border: 1px solid rgba(0,0,0,.125);\n  border-radius: .25rem;\n  padding: .5rem .75rem;\n  box-shadow: 0 .5rem 1rem rgba(0,0,0,.15);\n  max-width: 320px;\n  color: #212529;\n}\n';
      document.head.appendChild(style);
    }

    // Fallback popover implementation
    triggers.forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.preventDefault();
        // Close any existing custom popovers
        document.querySelectorAll('.custom-popover').forEach(function (p) { p.remove(); });

        var content = el.getAttribute('data-bs-content') || '';
        var pop = document.createElement('div');
        pop.className = 'custom-popover';
        pop.innerHTML = content;
        document.body.appendChild(pop);

        // Position to the right of the trigger when possible
        var rect = el.getBoundingClientRect();
        // Temporarily place off-screen to measure
        pop.style.top = '0px'; pop.style.left = '-9999px';
        var popRect = pop.getBoundingClientRect();
        var top = window.scrollY + rect.top + (rect.height - popRect.height) / 2;
        var left = window.scrollX + rect.right + 8;
        // If overflow right, place to the left
        if (left + popRect.width > window.scrollX + window.innerWidth) {
          left = window.scrollX + rect.left - popRect.width - 8;
        }
        // If still off-screen vertically, clamp
        if (top < window.scrollY + 8) { top = window.scrollY + 8; }
        if (top + popRect.height > window.scrollY + window.innerHeight - 8) { top = window.scrollY + window.innerHeight - popRect.height - 8; }

        pop.style.top = top + 'px';
        pop.style.left = left + 'px';

        // Close on outside click
        function onDocClick(ev) {
          if (!pop.contains(ev.target) && ev.target !== el) {
            pop.remove();
            document.removeEventListener('click', onDocClick);
            document.removeEventListener('keydown', onKey);
          }
        }
        function onKey(ev) { if (ev.key === 'Escape') { pop.remove(); document.removeEventListener('click', onDocClick); document.removeEventListener('keydown', onKey); } }
        setTimeout(function () { document.addEventListener('click', onDocClick); document.addEventListener('keydown', onKey); }, 0);
      });
      // keyboard access: Enter or Space opens
      el.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); el.click(); } });
    });

  });
})();
