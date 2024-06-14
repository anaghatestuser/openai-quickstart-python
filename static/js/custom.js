function displayLoading() {
    const loader = document.getElementById('loader');
    loader.style.display = "block";
}

// Toggle function to switch between dark and light mode, and save the preference
function toggleDarkMode() {
    const body = document.querySelector('body');

    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    }
}

// Toggle password visibility
function togglePasswordVisibility(id) {
    var x = document.getElementById(id);
    if (x.type === "password") {
        x.type = "text";
    } else {
        x.type = "password";
    }
}

// On page load, check the theme preference and apply it
document.addEventListener('DOMContentLoaded', function() {
    // Apply Dark mode
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme === 'dark') {
        document.querySelector('body').classList.add('dark-mode');
    } else {
        document.querySelector('body').classList.remove('dark-mode');
    }

    // Handle feedback form submission
    const feedbackForm = document.getElementById('feedback-form');

    if(feedbackForm) {
        feedbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
    
            console.log("Form submission triggered!"); // For debugging
            
            const reasons = document.querySelectorAll('.reason-input');
            let data = [];
            const ratingValue = parseInt(document.getElementById('rating').value);
    
            console.log("Rating:", ratingValue); // Check the rating value
    
            reasons.forEach((reason) => {
                if(reason.checked) {
                    data.push(reason.value);
                }
            });
    
            if(!ratingValue || ratingValue < 1 || ratingValue > 5) {
                alert("Please provide a valid rating between 1 and 5.");
                return;
            }
    
            if(data.length == 0 && !document.getElementById('feedback').value) {
                alert('Please select at least one reason or provide feedback text.');
                return;
            }
    
            const formData = new FormData(this);
    
            fetch('/submit_feedback', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);  // Display the response data for debugging
    
                if (data.status === 'error') {
                    alert(data.message);
                } else {
                    window.location.href = data.redirect_url;
                }
            })
            .catch(error => {
                console.error("Error submitting feedback:", error);  // This will display if there's an error with the fetch request.
            });
        });
    }

    // Initialize DataTable with sorting enabled on all columns
    $('#feedbackTable').DataTable({
        "order": [],
        "columnDefs": [
            { "orderable": true, "targets": [0, 1, 2, 3, 4] }
        ]
    });
});
