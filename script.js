// Mobile Navigation
const hamburger = document.getElementById('hamburger');
const navMenu = document.getElementById('nav-menu');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
    });
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const headerOffset = 80;
            const elementPosition = target.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// Navbar background change on scroll
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for scroll animations
document.addEventListener('DOMContentLoaded', () => {
    const animateElements = document.querySelectorAll('.experience-card, .room-card, .gallery-item, .contact-item');
    
    animateElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });
});

// Hero button interactions
document.addEventListener('DOMContentLoaded', () => {
    const exploreBtn = document.querySelector('.btn-primary');
    const videoBtn = document.querySelector('.btn-secondary');

    if (exploreBtn) {
        exploreBtn.addEventListener('click', () => {
            document.querySelector('#experiences').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    }

    if (videoBtn) {
        videoBtn.addEventListener('click', () => {
            // Placeholder for video modal or functionality
            alert('Video feature coming soon! Explore our beautiful cultural experiences in the meantime.');
        });
    }
});

// Contact form handling
document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.querySelector('.contact-form form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(this);
            const name = this.querySelector('input[type="text"]').value;
            const email = this.querySelector('input[type="email"]').value;
            const subject = this.querySelector('input[type="text"]:nth-of-type(2)').value;
            const message = this.querySelector('textarea').value;
            
            // Basic validation
            if (!name || !email || !message) {
                alert('Please fill in all required fields.');
                return;
            }
            
            // Email validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                alert('Please enter a valid email address.');
                return;
            }
            
            // Show success message
            alert('Thank you for your message! We will get back to you soon.');
            
            // Reset form
            this.reset();
        });
    }
});

// Gallery item interactions
document.addEventListener('DOMContentLoaded', () => {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach(item => {
        item.addEventListener('click', () => {
            // Placeholder for lightbox or modal functionality
            const title = item.querySelector('.overlay h4').textContent;
            alert(`Viewing: ${title}\n\nImage gallery feature coming soon!`);
        });
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero');
    const rate = scrolled * -0.5;
    
    if (hero) {
        hero.style.transform = `translateY(${rate}px)`;
    }
});

// Booking functionality
document.addEventListener('DOMContentLoaded', () => {
    const bookNowBtns = document.querySelectorAll('.book-now');
    
    bookNowBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            // Placeholder for booking system
            alert('Booking system coming soon! Please contact us directly for reservations.');
        });
    });
});

// Room card hover effects
document.addEventListener('DOMContentLoaded', () => {
    const roomCards = document.querySelectorAll('.room-card');
    
    roomCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(-5px) scale(1)';
        });
    });
});

// Experience card interactions
document.addEventListener('DOMContentLoaded', () => {
    const experienceCards = document.querySelectorAll('.experience-card');
    
    experienceCards.forEach((card, index) => {
        card.addEventListener('click', () => {
            const experiences = [
                'Onsen Ritual',
                'Tea Ceremony',
                'Calligraphy Workshop',
                'Garden Meditation',
                'Kaiseki Dining',
                'Volcanic Hiking'
            ];
            
            const experienceName = experiences[index] || 'Cultural Experience';
            alert(`Learn more about our ${experienceName}!\n\nDetailed information and booking available soon.`);
        });
    });
});

// Scroll indicator functionality
document.addEventListener('DOMContentLoaded', () => {
    const scrollIndicator = document.querySelector('.scroll-indicator');
    
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', () => {
            document.querySelector('#about').scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        });
    }
});

// Active navigation link highlighting
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const sectionTop = section.getBoundingClientRect().top;
        const sectionHeight = section.offsetHeight;
        
        if (sectionTop <= 100 && sectionTop + sectionHeight > 100) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${currentSection}`) {
            link.classList.add('active');
        }
    });
});

// Add active link styles
const style = document.createElement('style');
style.textContent = `
    .nav-link.active {
        color: var(--primary-color) !important;
    }
    .nav-link.active::after {
        width: 100% !important;
    }
`;
document.head.appendChild(style);

// Lazy loading for performance (placeholder for future images)
document.addEventListener('DOMContentLoaded', () => {
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    // Future implementation for actual images
                    observer.unobserve(img);
                }
            });
        });
        
        // Future: observe actual images
        // document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
    }
});

// Console welcome message
console.log(`
🏔️ Welcome to Aso Cultural Resort
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Experience the heart of Japan in the volcanic wonderland of Mount Aso.
Website developed with modern web technologies for optimal performance.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);
