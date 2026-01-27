/* ============================================
   PERSONAL WEBSITE JAVASCRIPT
   Handles mobile menu, smooth scrolling, and form submission
   ============================================ */

// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', function() {
    
    /* ============================================
       MOBILE MENU TOGGLE
       Opens and closes the navigation menu on mobile devices
       ============================================ */
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Toggle menu when hamburger is clicked
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }
    
    // Close menu when a nav link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });
    
    /* ============================================
       SMOOTH SCROLLING FOR ANCHOR LINKS
       Provides smooth scrolling effect when clicking navigation links
       ============================================ */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                const navbarHeight = document.querySelector('.navbar').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    /* ============================================
       ACTIVE NAVIGATION HIGHLIGHTING
       Highlights the current section in the navigation menu
       ============================================ */
    const sections = document.querySelectorAll('section[id]');
    
    function highlightNavigation() {
        const scrollPosition = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            const navLink = document.querySelector(`.nav-link[href="#${sectionId}"]`);
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                navLinks.forEach(link => link.classList.remove('active'));
                if (navLink) {
                    navLink.classList.add('active');
                }
            }
        });
    }
    
    // Run on scroll
    window.addEventListener('scroll', highlightNavigation);
    
    /* ============================================
       CONTACT FORM HANDLING
       Handles form submission (you'll need to configure with your backend)
       ============================================ */
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                message: document.getElementById('message').value
            };
            
            /* ============================================
               FORM SUBMISSION CONFIGURATION
               
               Option 1: Use a form service like Formspree, Netlify Forms, or EmailJS
               Replace the code below with your form service configuration
               
               Example with Formspree:
               fetch('https://formspree.io/f/YOUR_FORM_ID', {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify(formData)
               })
               
               Option 2: Send to your own backend
               fetch('/api/contact', {
                   method: 'POST',
                   headers: { 'Content-Type': 'application/json' },
                   body: JSON.stringify(formData)
               })
               
               Option 3: Use mailto (simple but limited)
               window.location.href = `mailto:your.email@example.com?subject=Contact from ${formData.name}&body=${formData.message}`;
               ============================================ */
            
            // For now, just log the data and show an alert
            console.log('Form submitted:', formData);
            alert('Thank you for your message! This is a demo form. To make it functional, configure the form submission in script.js');
            
            // Reset form
            contactForm.reset();
            
            /* 
            // Uncomment and modify this code when you're ready to connect to a real form service:
            
            fetch('YOUR_FORM_ENDPOINT_HERE', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                alert('Thank you! Your message has been sent.');
                contactForm.reset();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Sorry, there was an error sending your message. Please try emailing directly.');
            });
            */
        });
    }
    
    /* ============================================
       SCROLL ANIMATIONS
       Adds fade-in animations as elements come into view
       ============================================ */
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe project cards and publication items for animation
    document.querySelectorAll('.project-card, .publication-item').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
    
    /* ============================================
       DYNAMIC YEAR IN FOOTER
       Automatically updates the copyright year
       ============================================ */
    const footerYear = document.querySelector('.footer p');
    if (footerYear && footerYear.textContent.includes('2026')) {
        const currentYear = new Date().getFullYear();
        footerYear.textContent = footerYear.textContent.replace('2026', currentYear);
    }
});

/* ============================================
   UTILITY FUNCTIONS
   Helper functions you can use throughout your site
   ============================================ */

/**
 * Debounce function to limit how often a function is called
 * Useful for scroll and resize event listeners
 * 
 * @param {Function} func - The function to debounce
 * @param {number} wait - Time to wait in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Check if an element is in the viewport
 * 
 * @param {Element} element - The element to check
 * @returns {boolean} - True if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}
