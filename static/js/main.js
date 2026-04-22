// Theme Toggle and Reading Progress for Hugo Cloud CMS

(function() {
  // Theme Toggle Functionality
  const themeToggle = document.getElementById('themeBtn');
  const htmlElement = document.documentElement;
  
  // Check for saved theme preference or use system preference
  function getPreferredTheme() {
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
      return storedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  }
  
  // Apply theme to document
  function setTheme(theme) {
    htmlElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update button aria-label
    if (themeToggle) {
      const themeLabel = theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode';
      themeToggle.setAttribute('aria-label', themeLabel);
    }
  }
  
  // Initialize theme on page load
  function initTheme() {
    const theme = getPreferredTheme();
    setTheme(theme);
  }
  
  // Toggle theme when button clicked
  function toggleTheme() {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }
  
  // Set up theme toggle button
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  
  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
  
  // Reading Progress Bar
  const readingBarFill = document.getElementById('readingBar');
  
  function updateReadingProgress() {
    if (!readingBarFill) return;
    
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight - windowHeight;
    const scrolled = window.scrollY;
    const progress = (scrolled / documentHeight) * 100;
    
    readingBarFill.style.width = progress + '%';
  }
  
  // Update reading progress on scroll
  if (readingBarFill) {
    window.addEventListener('scroll', updateReadingProgress);
    window.addEventListener('resize', updateReadingProgress);
    updateReadingProgress(); // Initial update
  }
  
  // Initialize theme when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
  
  // Add class for when page is fully loaded
  window.addEventListener('load', () => {
    document.body.classList.add('loaded');
  });
  
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetElement = document.querySelector(targetId);
      
      if (targetElement) {
        targetElement.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
})();