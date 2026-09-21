(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const caja = document.getElementById('importar-link');
        if (!caja) return;

        const form = caja.querySelector('form');
        const boton = caja.querySelector('.importar-link-boton');
        const estado = document.getElementById('importar-estado');
        const publicar = document.getElementById('importar-publicar');

        function mostrar(texto, esError) {
            estado.textContent = texto;
            estado.classList.toggle('es-error', !!esError);
            estado.hidden = false;
        }

        form.addEventListener('submit', function (evento) {
            evento.preventDefault();
            const datos = new FormData(form);
            if (publicar.checked) datos.set('publicar', 'on');

            boton.disabled = true;
            const textoOriginal = boton.textContent;
            boton.textContent = 'Importando...';
            mostrar('Leyendo la publicación, bajando las fotos y escribiendo la descripción. Puede tardar hasta un minuto, no cierres esta página.');

            fetch(caja.dataset.url, {
                method: 'POST',
                body: datos,
                credentials: 'same-origin',
            })
                .then(function (resp) {
                    return resp.json().then(function (json) { return { ok: resp.ok, json: json }; });
                })
                .then(function (resultado) {
                    if (resultado.ok && resultado.json.url) {
                        mostrar('Listo, abriendo la propiedad importada...');
                        window.location.href = resultado.json.url;
                        return;
                    }
                    mostrar(resultado.json.error || 'No se pudo importar la propiedad.', true);
                })
                .catch(function () {
                    mostrar('Se cortó la conexión con el servidor. Revisá si la propiedad quedó cargada en el listado.', true);
                })
                .finally(function () {
                    boton.disabled = false;
                    boton.textContent = textoOriginal;
                });
        });
    });
})();
