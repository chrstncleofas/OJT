function showForm(type) {
    document.getElementById('button-container').style.display = 'none';

    document.getElementById('student-form').classList.remove('active');
    document.getElementById('coordinator-form').classList.remove('active');
    if (type === 'student') {
        document.getElementById('student-form').classList.add('active');
    } else if (type === 'coordinator') {
        document.getElementById('coordinator-form').classList.add('active');
    }
}
function goBack() {
    document.getElementById('student-form').classList.remove('active');
    document.getElementById('coordinator-form').classList.remove('active');
    document.getElementById('button-container').style.display = 'block';
    // Clear error messages
    document.getElementById('student-error-message').style.display = 'none';
    document.getElementById('coordinator-error-message').style.display = 'none';
}

// Handling form submissions with AJAX
document.getElementById('student-login-form').onsubmit = function(e) {
    e.preventDefault(); // Iwasan ang default na pag-submit ng form

    const formData = new FormData(this);
    fetch(this.action, {
        method: 'POST',
        body: formData
    }).then(response => response.json()).then(data => {
        if (data.error) {
            document.getElementById('student-error-message').innerText = data.error;
            document.getElementById('student-error-message').style.display = 'block'; // Ipakita ang error message
        } else if (data.redirect_url) {
            window.location.href = data.redirect_url; // I-redirect ang user
        }
    }).catch(error => console.error('Error:', error));
};

document.getElementById('coordinator-login-form').onsubmit = function(e) {
    e.preventDefault(); // Iwasan ang default na pag-submit ng form

    const formData = new FormData(this);
    fetch(this.action, {
        method: 'POST',
        body: formData
    }).then(response => response.json()).then(data => {
        if (data.error) {
            document.getElementById('coordinator-error-message').innerText = data.error;
            document.getElementById('coordinator-error-message').style.display = 'block'; // Ipakita ang error message
        } else if (data.redirect_url) {
            window.location.href = data.redirect_url; // I-redirect ang user
        }
    }).catch(error => console.error('Error:', error));
};