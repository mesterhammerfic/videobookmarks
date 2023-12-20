// handle buttons and form for adding tag
const deleteButtons = document.getElementsByClassName('button big delete');
var link;
for (button of deleteButtons){
    button.addEventListener('click', function (e) {
        if (window.confirm('Are you sure you want to delete this lookmark collection?')) {
            link = this.value;
            fetch(link, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json',
                }
            });
            location.reload();
        };
    });
};
