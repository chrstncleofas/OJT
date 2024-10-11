document.getElementById('id_image').addEventListener('change', function() {
    if (this.files && this.files[0]) {
        document.getElementById('timeInBtn').disabled = false;
        document.getElementById('timeOutBtn').disabled = false;
    }
});
function previewImage(event) {
    var preview = document.getElementById('preview');
    var file = document.getElementById('id_image').files[0];
    var reader = new FileReader();
    reader.onload = function() {
        preview.src = reader.result;
        preview.style.display = 'block';
    }
    if (file) {
        reader.readAsDataURL(file);
    }
}
document.getElementById('id_image').addEventListener('change', previewImage);