// Questionnaire Navigation Script with Flask Integration
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('assessmentForm');
    const sections = document.querySelectorAll('.form-section');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const progressBar = document.getElementById('progressBar');
    const currentStepSpan = document.getElementById('currentStep');
    const totalStepsSpan = document.getElementById('totalSteps');
    
    let currentSection = 0;
    const totalSections = sections.length;
    
    // Set total steps
    totalStepsSpan.textContent = totalSections;
    
    // Initialize
    showSection(currentSection);
    
    // Next button click
    nextBtn.addEventListener('click', function() {
        if (validateSection(currentSection)) {
            currentSection++;
            if (currentSection < totalSections) {
                showSection(currentSection);
            }
        } else {
            alert('Please answer all required questions before proceeding.');
        }
    });
    
    // Previous button click
    prevBtn.addEventListener('click', function() {
        currentSection--;
        if (currentSection >= 0) {
            showSection(currentSection);
        }
    });
    
    // Form submission - MODIFIED FOR FLASK
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (validateSection(currentSection)) {
            // Show loading state
            submitBtn.textContent = 'Processing...';
            submitBtn.disabled = true;
            
            // Collect form data
            const formData = new FormData(form);
            const data = {};
            
            // Convert FormData to JSON
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Send to Flask backend
            fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // Store results in sessionStorage
                    sessionStorage.setItem('riskResults', JSON.stringify(result));
                    
                    // Redirect to results page
                    window.location.href = '/results';
                } else {
                    throw new Error(result.error || 'Prediction failed');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing your assessment. Please try again.');
                submitBtn.textContent = 'Submit Assessment';
                submitBtn.disabled = false;
            });
        } else {
            alert('Please complete all required fields and agree to the terms.');
        }
    });
    
    function showSection(index) {
        // Hide all sections
        sections.forEach(section => {
            section.classList.remove('active');
        });
        
        // Show current section
        sections[index].classList.add('active');
        
        // Update progress bar
        const progress = ((index + 1) / totalSections) * 100;
        progressBar.style.width = progress + '%';
        
        // Update step counter
        currentStepSpan.textContent = index + 1;
        
        // Handle button visibility
        if (index === 0) {
            prevBtn.style.display = 'none';
        } else {
            prevBtn.style.display = 'inline-block';
        }
        
        if (index === totalSections - 1) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'inline-block';
        } else {
            nextBtn.style.display = 'inline-block';
            submitBtn.style.display = 'none';
        }
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    function validateSection(index) {
        const section = sections[index];
        const requiredInputs = section.querySelectorAll('input[required], select[required]');
        
        // For radio buttons, check if at least one in each group is selected
        const radioGroups = {};
        requiredInputs.forEach(input => {
            if (input.type === 'radio') {
                const name = input.name;
                if (!radioGroups[name]) {
                    radioGroups[name] = false;
                }
                if (input.checked) {
                    radioGroups[name] = true;
                }
            } else if (input.type === 'checkbox') {
                if (!input.checked) {
                    return false;
                }
            } else {
                if (!input.value.trim()) {
                    return false;
                }
            }
        });
        
        // Check all radio groups are answered
        for (let group in radioGroups) {
            if (!radioGroups[group]) {
                return false;
            }
        }
        
        // Check checkboxes
        const checkboxes = section.querySelectorAll('input[type="checkbox"][required]');
        for (let checkbox of checkboxes) {
            if (!checkbox.checked) {
                return false;
            }
        }
        
        return true;
    }
    
    // Add visual feedback for selected options
    const radioOptions = document.querySelectorAll('.radio-option');
    radioOptions.forEach(option => {
        const radio = option.querySelector('input[type="radio"]');
        
        radio.addEventListener('change', function() {
            // Remove selected class from all options in this group
            const groupName = this.name;
            const groupOptions = document.querySelectorAll(`input[name="${groupName}"]`);
            groupOptions.forEach(opt => {
                opt.closest('.radio-option').style.borderColor = '';
                opt.closest('.radio-option').style.backgroundColor = '';
            });
            
            // Add selected style to chosen option
            if (this.checked) {
                option.style.borderColor = 'var(--primary-green)';
                option.style.backgroundColor = 'var(--light-green)';
            }
        });
    });
});