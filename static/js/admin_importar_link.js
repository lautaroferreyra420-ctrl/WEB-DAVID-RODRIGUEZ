(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const caja = document.getElementById('importar-link');
        if (!caja) return;

        const form = caja.querySelector('form');
        const boton = caja.querySelector('.importar-link-boton');
        const estado = document.getElementById('importar-estado');
        const publicar = document.getElementById('importar-publicar');
        const urlListado = caja.dataset.urlListado;

        function mostrar(texto, esError) {
            estado.replaceChildren(document.createTextNode(texto));
            estado.classList.toggle('es-error', !!esError);
            estado.hidden = false;
        }

        function enviar(datos) {
            return fetch(caja.dataset.url, { method: 'POST', body: datos, credentials: 'same-origin' })
                .then(function (resp) {
                    return resp.json().then(function (json) { return { ok: resp.ok, json: json }; });
                });
        }

        function datosBase() {
            const datos = new FormData(form);
            if (publicar.checked) datos.set('publicar', 'on');
            return datos;
        }

        function liberar(textoOriginal) {
            boton.disabled = false;
            boton.textContent = textoOriginal;
        }

        // El link tenía varias propiedades: se importa cada una por separado, mostrando el avance
        function importarListado(fichas, aviso, textoOriginal) {
            const lista = document.createElement('ul');
            lista.className = 'importar-lista';
            const titulo = document.createElement('p');
            titulo.className = 'importar-lista-titulo';
            estado.replaceChildren(titulo, lista);
            estado.classList.remove('es-error');
            estado.hidden = false;

            const filas = fichas.map(function (ficha) {
                const fila = document.createElement('li');
                fila.className = 'pendiente';
                const nombre = ficha.texto && ficha.texto.length > 3 ? ficha.texto : decodeURIComponent(ficha.url.split('/').pop().slice(0, 80));
                fila.textContent = nombre;
                lista.appendChild(fila);
                return fila;
            });

            let importadas = 0;
            let omitidas = 0;
            const detalle = { pk: null };

            function actualizarTitulo(hechas) {
                titulo.textContent = 'Este link tiene ' + fichas.length + ' propiedades. Importando ' + Math.min(hechas + 1, fichas.length) +
                    ' de ' + fichas.length + '... (cada una tarda unos 30 segundos, no cierres esta página)' + (aviso ? ' ' + aviso : '');
            }

            function marcar(fila, clase, texto) {
                fila.className = clase;
                if (texto) {
                    const nota = document.createElement('small');
                    nota.textContent = ' — ' + texto;
                    fila.appendChild(nota);
                }
            }

            function paso(i) {
                if (i >= fichas.length) return Promise.resolve();
                actualizarTitulo(i);
                filas[i].className = 'en-curso';
                const datos = datosBase();
                datos.set('link', fichas[i].url);
                datos.set('ficha', '1');
                datos.set('sin_mensajes', '1');
                return enviar(datos)
                    .then(function (res) {
                        if (res.ok && res.json.ok) {
                            importadas += 1;
                            detalle.pk = res.json.pk;
                            const avisos = res.json.avisos && res.json.avisos.length ? ' (revisar: ' + res.json.avisos.join(' ') + ')' : '';
                            filas[i].textContent = res.json.direccion;
                            marcar(filas[i], 'hecha', res.json.fotos + ' foto(s)' + avisos);
                        } else {
                            omitidas += 1;
                            marcar(filas[i], 'omitida', res.json.error || 'No se pudo importar');
                        }
                    })
                    .catch(function () {
                        omitidas += 1;
                        marcar(filas[i], 'omitida', 'se cortó la conexión');
                    })
                    .then(function () { return paso(i + 1); });
            }

            paso(0).then(function () {
                titulo.textContent = 'Listo: se importaron ' + importadas + ' propiedad(es)' +
                    (omitidas ? ' y se omitieron ' + omitidas + ' (ya estaban cargadas o hubo un error)' : '') +
                    '. Quedan como ' + (publicar.checked ? 'publicadas' : 'borrador para que las revises') + '.';
                if (importadas) {
                    const enlace = document.createElement('a');
                    enlace.className = 'importar-link-boton importar-lista-ver';
                    enlace.href = urlListado + (publicar.checked ? '' : '?esta_disponible__exact=0');
                    enlace.textContent = publicar.checked ? 'Ver las propiedades' : 'Ver los borradores';
                    estado.appendChild(enlace);
                }
                liberar(textoOriginal);
            });
        }

        form.addEventListener('submit', function (evento) {
            evento.preventDefault();
            boton.disabled = true;
            const textoOriginal = boton.textContent;
            boton.textContent = 'Importando...';
            mostrar('Leyendo la publicación, bajando las fotos y escribiendo la descripción. Puede tardar hasta un minuto, no cierres esta página.');

            enviar(datosBase())
                .then(function (resultado) {
                    if (resultado.ok && resultado.json.listado) {
                        importarListado(resultado.json.fichas, resultado.json.aviso, textoOriginal);
                        return;
                    }
                    if (resultado.ok && resultado.json.url) {
                        mostrar('Listo, abriendo la propiedad importada...');
                        window.location.href = resultado.json.url;
                        return;
                    }
                    mostrar(resultado.json.error || 'No se pudo importar la propiedad.', true);
                    liberar(textoOriginal);
                })
                .catch(function () {
                    mostrar('Se cortó la conexión con el servidor. Revisá si la propiedad quedó cargada en el listado.', true);
                    liberar(textoOriginal);
                });
        });
    });
})();
