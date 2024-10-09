// Function to preview image
const csrfToken = "{{ csrf_token }}";
function previewImage(event) {
    var preview = document.getElementById('preview');
    var file = document.getElementById('id_image').files[0];
    var reader = new FileReader();
    reader.onload = function () {
        preview.src = reader.result;
        preview.style.display = 'block';
    }
    if (file) {
        reader.readAsDataURL(file);
    }
}

function validatePassword(studentId) {
    var inputPasswordElement = document.getElementById('adminPassword' + studentId);
    if (inputPasswordElement === null) {
        console.error('Cannot find element with ID:', 'adminPassword' + studentId);
        return;
    }

    var inputPassword = inputPasswordElement.value;
    if (!inputPassword) {
        alert('Please enter the admin password.');
        return;
    }

    fetch("/coordinator/validate_admin_password/", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ password: inputPassword })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            archiveStudent(studentId);
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

function archiveStudent(studentId) {
    const url = `/coordinator/archivedStudent/${studentId}/`;

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ studentID: studentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(data.message);
            location.reload();
        } else {
            alert(data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}


// Event listener for image preview
document.getElementById('id_image').addEventListener('change', previewImage);

// Event listener for navbar toggler
$(".navbar-toggler").click(function (e) {
    e.preventDefault();
    $("#wrapper").toggleClass("toggled");
});
