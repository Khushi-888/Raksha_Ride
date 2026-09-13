/**
 * RakshaRide Motion UI Controller
 * Powered by Motion & 21st.dev Component Interactions
 */

(function () {
  'use strict';

  // Wait for DOM content loaded
  document.addEventListener('DOMContentLoaded', () => {
    initScrollAnimations();
    initHoverTiltEffects();
    initSafetyRadarPulse();
    initShimmerButtons();
    initFloatingNavbar();
  });

  /**
   * Scroll-triggered entrance animations (Stagger & Fade Up)
   */
  function initScrollAnimations() {
    const observerOptions = {
      root: null,
      rootMargin: '0px 0px -50px 0px',
      threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('motion-appear');
          // Optional: unobserve once animated if desired
        }
      });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.motion-fade-up, .motion-scale-in, .how-step, .feature-card, .stat-card');
    animatedElements.forEach((el, idx) => {
      if (!el.classList.contains('motion-fade-up') && !el.classList.contains('motion-scale-in')) {
        el.classList.add('motion-fade-up');
      }
      // Auto assign stagger delay
      const staggerClass = `motion-stagger-${(idx % 4) + 1}`;
      el.classList.add(staggerClass);
      observer.observe(el);
    });
  }

  /**
   * 3D Tilt & Micro-spring interaction for motion cards
   */
  function initHoverTiltEffects() {
    const cards = document.querySelectorAll('.motion-glow-card, .floating-card, .feature-card');
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * -5; // max 5 deg tilt
        const rotateY = ((x - centerX) / centerX) * 5;

        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)';
      });
    });
  }

  /**
   * Live Safety Radar status pulse update
   */
  function initSafetyRadarPulse() {
    const radarBadges = document.querySelectorAll('.safety-radar-container');
    radarBadges.forEach(badge => {
      const textEl = badge.querySelector('.radar-text');
      if (textEl && !textEl.dataset.initialized) {
        textEl.dataset.initialized = "true";
        // Pulse text subtlety
        setInterval(() => {
          textEl.style.opacity = '0.75';
          setTimeout(() => textEl.style.opacity = '1', 400);
        }, 3000);
      }
    });
  }

  /**
   * Shimmer motion buttons interactive click feedback
   */
  function initShimmerButtons() {
    const buttons = document.querySelectorAll('.shimmer-btn, .btn-primary');
    buttons.forEach(btn => {
      btn.addEventListener('mousedown', () => {
        btn.style.transform = 'scale(0.96)';
      });
      btn.addEventListener('mouseup', () => {
        btn.style.transform = '';
      });
    });
  }

  /**
   * Floating Navbar scroll reaction
   */
  function initFloatingNavbar() {
    const nav = document.querySelector('.navbar, .motion-floating-nav');
    if (!nav) return;

    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > 60) {
        nav.classList.add('scrolled-nav');
        if (currentScrollY > lastScrollY && currentScrollY > 200) {
          // Scrolling down - slight hide/compact
          nav.style.transform = 'translateY(-10px) scale(0.98)';
        } else {
          // Scrolling up - return
          nav.style.transform = 'translateY(0) scale(1)';
        }
      } else {
        nav.classList.remove('scrolled-nav');
        nav.style.transform = 'translateY(0) scale(1)';
      }
      lastScrollY = currentScrollY;
    });
  }

  // Export to global scope
  window.RakshaMotion = {
    initScrollAnimations,
    initHoverTiltEffects
  };
})();
