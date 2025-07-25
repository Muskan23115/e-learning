// Sparkle effect
const glitter = document.querySelector('.background-glitter');
if (glitter) {
    for (let i = 0; i < 40; i++) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        sparkle.style.position = 'absolute';
        sparkle.style.left = Math.random() * 100 + 'vw';
        sparkle.style.top = Math.random() * 100 + 'vh';
        sparkle.style.width = sparkle.style.height = (Math.random() * 6 + 4) + 'px';
        sparkle.style.background = 'radial-gradient(circle, #fff 60%, #e75480 100%)';
        sparkle.style.opacity = Math.random() * 0.7 + 0.3;
        sparkle.style.borderRadius = '50%';
        sparkle.style.filter = 'blur(0.5px)';
        sparkle.style.animation = `floatSparkle ${Math.random() * 6 + 4}s ease-in-out infinite`;
        glitter.appendChild(sparkle);
    }
}
// Smooth scroll for Ask Doubts
const askBtn = document.querySelector('.cta-buttons .secondary');
if (askBtn) {
    askBtn.addEventListener('click', function(e) {
        e.preventDefault();
        document.getElementById('contact').scrollIntoView({ behavior: 'smooth' });
    });
}
// Floating sparkles for dashboard
const dashSection = document.querySelector('.dashboard-section');
if (dashSection) {
    for (let i = 0; i < 18; i++) {
        const sparkle = document.createElement('div');
        sparkle.className = 'dashboard-sparkle';
        sparkle.style.left = Math.random() * 100 + '%';
        sparkle.style.top = Math.random() * 100 + '%';
        sparkle.style.width = sparkle.style.height = (Math.random() * 8 + 6) + 'px';
        sparkle.style.opacity = Math.random() * 0.5 + 0.3;
        sparkle.style.animationDuration = (Math.random() * 4 + 5) + 's';
        dashSection.appendChild(sparkle);
    }
}
// Sparkle animation
const style = document.createElement('style');
style.innerHTML = `
@keyframes floatSparkle {
    0% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-30px) scale(1.2); }
    100% { transform: translateY(0) scale(1); }
}
.sparkle {
    pointer-events: none;
    position: absolute;
    z-index: 1;
}
`;
document.head.appendChild(style); 