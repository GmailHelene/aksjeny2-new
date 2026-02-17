// Achievement tracking library for Aksjeradar
let achievementTracking = {
    // Show achievement popup
    showAchievementPopup: function(achievement) {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.achievement-toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'achievement-toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1060';
            document.body.appendChild(toastContainer);
        }

        // Create toast for achievement
        const toast = document.createElement('div');
        toast.className = `achievement-toast toast show align-items-center text-white border-0 mb-2`;
        toast.style.backgroundColor = achievement.badge_color || '#198754';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        // Add achievement content
        toast.innerHTML = `
            <div class="d-flex align-items-center p-3">
                <div class="achievement-icon me-3">
                    <i class="bi bi-${achievement.icon || 'trophy'} fs-3"></i>
                </div>
                <div class="achievement-content flex-grow-1">
                    <h6 class="mb-0">Ny prestasjon låst opp!</h6>
                    <div class="achievement-name">${achievement.name}</div>
                    <small class="text-white-50">${achievement.description}</small>
                </div>
                <div class="achievement-points ms-3 text-center">
                    <div class="points-value fw-bold">+${achievement.points}</div>
                    <small class="text-white-50">poeng</small>
                </div>
            </div>`;

        // Add to container
        toastContainer.appendChild(toast);

        // Remove after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);

        // Play achievement sound if available
        const achievementSound = document.getElementById('achievement-sound');
        if (achievementSound) {
            achievementSound.play().catch(() => {});
        }
    },

    // Track achievement progress
    trackAchievement: async function(type, increment = 1) {
        try {
            // Call achievement API
            const response = await fetch('/achievements/api/update_stat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                },
                body: JSON.stringify({ type, increment })
            });

            // Parse response
            const data = await response.json();

            // Handle demo mode
            if (!response.ok) {
                if (response.status === 401 && data.demo_mode) {
                    // Silently ignore achievement tracking for demo users
                    return;
                }
                throw new Error(data.error || 'Achievement tracking failed');
            }

            // Show notifications for new achievements
            if (data.success && data.new_achievements) {
                data.new_achievements.forEach(achievement => {
                    this.showAchievementPopup(achievement);
                });
            }

            return data;
        } catch (error) {
            // Log error but don't throw - achievement failures shouldn't break the app
            console.warn('Achievement tracking error:', error);
            return { success: false, error: error.message };
        }
    }
};

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = achievementTracking;
}
