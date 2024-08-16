$(document).ready(function() {
    $('#passwordModal').on('show.bs.modal', function(event) {
        var button = $(event.relatedTarget);
        var studentId = button.data('student-id');
        var modal = $(this);
        modal.find('#studentId').val(studentId);
    });

    $('#validatePassword').on('click', function() {
        var username = $('#adminUsername').val();
        var password = $('#adminPassword').val();
        var studentId = $('#studentId').val();
        var csrfToken = getCookie('csrftoken');

        $.ajax({
            url: '/archivedStudent/' + studentId + '/',
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: {
                'username': username,
                'password': password
            },
            success: function(response) {
                if (response.status === 'success') {
                    $('#passwordModal').modal('hide');
                    $('#confirmationModal').modal('show');
                    $('#confirmArchive').data('student-id', studentId);
                } else {
                    alert(response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Error: ' + error);
            }
        });
    });

    $('#confirmArchive').on('click', function() {
        var studentId = $(this).data('student-id');
        var csrfToken = getCookie('csrftoken');

        $.ajax({
            url: '/archivedStudent/' + studentId + '/',
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            },
            data: {
                'confirm': true
            },
            success: function(response) {
                alert('Student archived successfully');
                location.reload();
            },
            error: function(xhr, status, error) {
                alert('Error: ' + error);
            }
        });
    });

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
