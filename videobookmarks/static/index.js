// handle buttons and form for adding tag
const deleteButtons = document.getElementsByClassName('button big delete');
for (button of deleteButtons){
    button.addEventListener('click', (event) => {
        var link = button.value;
        fetch(link, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
            }
        });
    });
};
