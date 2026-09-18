(function () {
    function getCookie(name) {
        const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return match ? decodeURIComponent(match.pop()) : '';
    }

    function construirUrl() {
        const match = window.location.pathname.match(/^(.*\/propiedad\/)/);
        return (match ? match[1] : '/admin/propiedades/propiedad/') + 'generar-descripcion-ia/';
    }

    function valorDe(id) {
        const el = document.getElementById(id);
        return el ? el.value : '';
    }

    function textoSeleccionado(id) {
        const el = document.getElementById(id);
        if (!el || el.selectedIndex < 0) return '';
        return el.options[el.selectedIndex].text.trim();
    }

    document.addEventListener('DOMContentLoaded', function () {
        const textarea = document.getElementById('id_descripcion');
        if (!textarea) return;

        const boton = document.createElement('button');
        boton.type = 'button';
        boton.textContent = '✨ Generar descripción con IA';
        boton.className = 'btn-generar-ia';

        const ayuda = document.createElement('p');
        ayuda.className = 'ayuda-generar-ia';
        ayuda.textContent = 'Completá dirección, tipo, precio y amenidades (o escribí un borrador acá abajo) y generá una descripción lista para publicar. Siempre podés editarla después.';

        const botonPublicar = document.createElement('button');
        botonPublicar.type = 'submit';
        botonPublicar.name = '_save';
        botonPublicar.className = 'btn-publicar-ia';
        botonPublicar.textContent = '💾 Guardar y publicar';
        botonPublicar.title = 'Guarda toda la propiedad con los datos actuales del formulario, sin tener que bajar hasta el final de la página.';

        textarea.parentNode.insertBefore(ayuda, textarea);
        textarea.parentNode.insertBefore(boton, textarea);
        textarea.parentNode.insertBefore(botonPublicar, textarea.nextSibling);

        boton.addEventListener('click', function () {
            const datos = {
                direccion: valorDe('id_direccion'),
                tipo_propiedad: textoSeleccionado('id_tipo_propiedad'),
                estado: textoSeleccionado('id_estado'),
                precio: valorDe('id_precio'),
                moneda: valorDe('id_moneda'),
                ambientes: valorDe('id_ambientes'),
                dormitorios: valorDe('id_dormitorios'),
                banos: valorDe('id_banos'),
                metros_cuadrados: valorDe('id_metros_cuadrados'),
                amenidades: valorDe('id_amenidades'),
                notas: textarea.value,
            };

            boton.disabled = true;
            const textoOriginal = boton.textContent;
            boton.textContent = 'Generando...';

            fetch(construirUrl(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: new URLSearchParams(datos).toString(),
            })
                .then(function (resp) {
                    return resp.json().then(function (data) {
                        return { ok: resp.ok, data: data };
                    });
                })
                .then(function (resultado) {
                    if (resultado.ok) {
                        textarea.value = resultado.data.descripcion;
                    } else {
                        alert(resultado.data.error || 'No se pudo generar la descripción.');
                    }
                })
                .catch(function () {
                    alert('No se pudo conectar con el servicio de IA.');
                })
                .finally(function () {
                    boton.disabled = false;
                    boton.textContent = textoOriginal;
                });
        });
    });
})();
