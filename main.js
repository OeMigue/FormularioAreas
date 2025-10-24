const boton = document.getElementById('elBoton');

boton.addEventListener('click', () => {
    Swal.fire({
        title: "¿Desea guardar los cambios?",
        showDenyButton: true,
        showCancelButton: true,
        confirmButtonText: "Guardar",
        denyButtonText: `No guardar`
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire("Guardado con éxito!", "", "success");
        } else if (result.isDenied) {
            Swal.fire("Los registros no fueron guardados :(", "", "info");
        }
    });
});
