// Aviso de cookies, "guardar propiedad", alertas de búsqueda y ventana de novedades.
// Todo con consentimiento: no se guarda nada de la persona hasta que ella lo acepta o deja su contacto.
(function () {
    const config = document.getElementById('dr-config');
    if (!config) return;

    const COOKIE_CONSENT = 'dr_consent';
    const CLAVE_VISTOS = 'dr_vistos';
    const CLAVE_POPUP_HASTA = 'dr_popup_hasta';
    const DIAS_SIN_POPUP = 7;
    const PROPIEDADES_PARA_POPUP = 5;   // cuántas propiedades distintas tiene que mirar antes de que aparezca la ventana

    const $ = (id) => document.getElementById(id);
    const csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
    let esInteresado = config.dataset.esInteresado === '1';
    let modalAbierto = false;
    let contexto = null;   // { tipo, propiedadId, filtros, boton }

    // ---------------------------------------------------------------- helpers

    function leerCookie(nombre) {
        const m = document.cookie.match('(^|;)\\s*' + nombre + '\\s*=\\s*([^;]+)');
        return m ? decodeURIComponent(m.pop()) : '';
    }

    function guardarCookie(nombre, valor) {
        const seguro = location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = nombre + '=' + encodeURIComponent(valor) + '; max-age=31536000; path=/; SameSite=Lax' + seguro;
    }

    function almacenamiento(operacion, clave, valor) {
        try {
            if (operacion === 'get') return JSON.parse(localStorage.getItem(clave));
            localStorage.setItem(clave, JSON.stringify(valor));
        } catch (e) { return null; }
    }

    function post(url, datos) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            credentials: 'same-origin',
            body: JSON.stringify(datos || {}),
        }).then((r) => r.json().then((json) => ({ ok: r.ok, status: r.status, json })));
    }

    // ---------------------------------------------------------------- aviso de cookies

    const aviso = $('dr-cookies');
    function elegirCookies(eleccion) {
        guardarCookie(COOKIE_CONSENT, eleccion);
        aviso.hidden = true;
        if (eleccion === 'all') iniciarSeguimientoLocal();
    }
    if (aviso) {
        if (!leerCookie(COOKIE_CONSENT)) {
            setTimeout(function () { aviso.hidden = false; }, 700);
        }
        aviso.querySelectorAll('[data-cookies]').forEach(function (b) {
            b.addEventListener('click', function () { elegirCookies(b.dataset.cookies); });
        });
    }

    // ---------------------------------------------------------------- ventana de contacto

    const modal = $('dr-modal');
    const formulario = $('dr-form');
    const errorCaja = $('dr-error');

    const TEXTOS = {
        favorito: {
            titulo: 'Guardá esta propiedad',
            texto: 'Dejanos tu contacto y te avisamos si baja de precio, se reserva o se vende.',
            boton: 'Guardar y avisarme',
            icono: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
        },
        alerta: {
            titulo: 'Te avisamos cuando entre algo así',
            texto: 'Dejanos tu contacto y te escribimos apenas entre una propiedad nueva para esta búsqueda:',
            boton: 'Avisarme',
            icono: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
        },
        popup: {
            titulo: '¿No encontraste lo que buscás?',
            texto: 'Dejanos tu contacto y te avisamos cuando entren propiedades como las que estuviste mirando.',
            boton: 'Quiero recibir novedades',
            icono: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
        },
    };

    function abrirModal(ctx) {
        if (modalAbierto || !modal) return;
        contexto = ctx;
        modalAbierto = true;
        const t = TEXTOS[ctx.tipo];
        $('dr-modal-titulo').textContent = t.titulo;
        $('dr-modal-texto').textContent = t.texto;
        $('dr-modal-icono').innerHTML = t.icono;
        $('dr-enviar').textContent = t.boton;
        const resumen = $('dr-modal-resumen');
        if (ctx.resumen) { resumen.textContent = ctx.resumen; resumen.hidden = false; } else { resumen.hidden = true; }
        errorCaja.hidden = true;
        $('dr-modal-formulario').hidden = false;
        $('dr-modal-ok').hidden = true;
        modal.hidden = false;
        document.body.classList.add('dr-modal-abierto');
        if (aviso) aviso.hidden = true;
        setTimeout(function () { formulario.email.focus(); }, 50);
    }

    function cerrarModal(recordarPopup) {
        if (!modal || modal.hidden) return;
        modal.hidden = true;
        modalAbierto = false;
        document.body.classList.remove('dr-modal-abierto');
        if (recordarPopup !== false && contexto && contexto.tipo === 'popup') posponerPopup();
        if (aviso && !leerCookie(COOKIE_CONSENT)) aviso.hidden = false;
    }

    if (modal) {
        modal.querySelectorAll('[data-cerrar]').forEach(function (e) {
            e.addEventListener('click', function () { cerrarModal(); });
        });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') cerrarModal(); });
    }

    if (formulario) {
        formulario.addEventListener('submit', function (evento) {
            evento.preventDefault();
            const datos = {
                tipo: contexto.tipo,
                email: formulario.email.value.trim(),
                telefono: formulario.telefono.value.trim(),
                website: formulario.website.value,
                acepta: formulario.acepta.checked,
                propiedad_id: contexto.propiedadId || '',
                filtros: contexto.filtros || {},
            };
            const boton = $('dr-enviar');
            const textoBoton = boton.textContent;
            errorCaja.hidden = true;
            boton.disabled = true;
            boton.textContent = 'Enviando...';

            post(config.dataset.urlRegistrar, datos)
                .then(function (res) {
                    if (!res.ok) {
                        errorCaja.textContent = res.json.error || 'No pudimos guardar tus datos. Probá de nuevo.';
                        errorCaja.hidden = false;
                        return;
                    }
                    esInteresado = true;
                    formulario.reset();
                    $('dr-ok-texto').textContent = res.json.mensaje;
                    $('dr-modal-formulario').hidden = true;
                    $('dr-modal-ok').hidden = false;
                    if (contexto.tipo === 'favorito') marcarGuardado(contexto.propiedadId, true);
                    posponerPopup(365);
                    setTimeout(function () { cerrarModal(false); }, 2600);
                })
                .catch(function () {
                    errorCaja.textContent = 'Se cortó la conexión. Probá de nuevo.';
                    errorCaja.hidden = false;
                })
                .finally(function () {
                    boton.disabled = false;
                    boton.textContent = textoBoton;
                });
        });
    }

    // ---------------------------------------------------------------- guardar propiedad (corazón)

    function marcarGuardado(id, guardado) {
        document.querySelectorAll('[data-guardar="' + id + '"]').forEach(function (b) {
            b.classList.toggle('guardado', guardado);
            b.setAttribute('aria-pressed', guardado ? 'true' : 'false');
            const etiqueta = b.querySelector('.btn-guardar-texto');
            if (etiqueta) etiqueta.textContent = guardado ? 'Guardada' : 'Guardar';
        });
    }

    document.addEventListener('click', function (e) {
        const boton = e.target.closest('[data-guardar]');
        if (!boton) return;
        e.preventDefault();
        const id = boton.dataset.guardar;
        if (!esInteresado) {
            abrirModal({ tipo: 'favorito', propiedadId: id });
            return;
        }
        post(config.dataset.urlFavorito.replace('/0/', '/' + id + '/'))
            .then(function (res) {
                if (res.status === 401) { esInteresado = false; abrirModal({ tipo: 'favorito', propiedadId: id }); return; }
                if (res.ok) marcarGuardado(id, res.json.guardado);
            });
    });

    // ---------------------------------------------------------------- alerta de búsqueda

    function filtrosDelFormulario() {
        const filtros = {};
        const campos = ['estado', 'tipo_propiedad', 'ubicacion_texto', 'precio_min', 'precio_max', 'metros_cuadrados_min', 'ambientes_min'];
        const barra = document.getElementById('filter-bar');
        const form = barra ? barra.closest('form') : null;
        if (!form) return filtros;
        campos.forEach(function (nombre) {
            const el = form.elements[nombre];
            if (el && !el.disabled && String(el.value).trim()) filtros[nombre] = String(el.value).trim();
        });
        return filtros;
    }

    function resumenFiltros(f) {
        const tipos = { Casa: 'Casas', Depto: 'Departamentos', Local: 'Locales', Terreno: 'Terrenos' };
        const partes = [(tipos[f.tipo_propiedad] || 'Propiedades') + (f.estado ? ' en ' + f.estado : '')];
        if (f.ubicacion_texto) partes.push(f.ubicacion_texto);
        const moneda = f.estado === 'Alquiler' ? '$' : 'USD';
        const miles = function (v) { const n = parseInt(v, 10); return isNaN(n) ? v : n.toLocaleString('es-AR'); };
        if (f.precio_min && f.precio_max) partes.push(moneda + ' ' + miles(f.precio_min) + ' a ' + miles(f.precio_max));
        else if (f.precio_max) partes.push('hasta ' + moneda + ' ' + miles(f.precio_max));
        else if (f.precio_min) partes.push('desde ' + moneda + ' ' + miles(f.precio_min));
        if (f.ambientes_min) partes.push(f.ambientes_min + '+ ambientes');
        if (f.metros_cuadrados_min) partes.push(f.metros_cuadrados_min + '+ m²');
        return partes.join(' · ');
    }

    document.addEventListener('click', function (e) {
        const boton = e.target.closest('[data-alerta]');
        if (!boton) return;
        e.preventDefault();
        let filtros;
        try { filtros = JSON.parse(boton.dataset.filtros || ''); } catch (err) { filtros = null; }
        if (!filtros || !Object.keys(filtros).length) filtros = filtrosDelFormulario();
        abrirModal({ tipo: 'alerta', filtros: filtros, resumen: boton.dataset.resumen || resumenFiltros(filtros) });
    });

    // ---------------------------------------------------------------- recorrido local y ventana de novedades

    function posponerPopup(dias) {
        almacenamiento('set', CLAVE_POPUP_HASTA, Date.now() + (dias || DIAS_SIN_POPUP) * 86400000);
    }

    function iniciarSeguimientoLocal() {
        if (leerCookie(COOKIE_CONSENT) !== 'all') return;
        const ctx = $('dr-ctx');
        let vistos = almacenamiento('get', CLAVE_VISTOS) || { ids: [], ultimo: null };
        if (ctx) {
            const id = ctx.dataset.propiedadId;
            if (id && vistos.ids.indexOf(id) === -1) vistos.ids.push(id);
            vistos.ultimo = { estado: ctx.dataset.estado, tipo_propiedad: ctx.dataset.tipo };
            almacenamiento('set', CLAVE_VISTOS, vistos);
        }

        // Ventana de novedades: tras ver 5 propiedades distintas, una sola vez cada 7 días, y nunca a quien ya dejó su contacto
        const pospuesto = almacenamiento('get', CLAVE_POPUP_HASTA) || 0;
        if (esInteresado || Date.now() < pospuesto || vistos.ids.length < PROPIEDADES_PARA_POPUP || !vistos.ultimo) return;
        setTimeout(function () {
            if (modalAbierto || esInteresado) return;
            const filtros = {};
            if (vistos.ultimo.estado) filtros.estado = vistos.ultimo.estado;
            if (vistos.ultimo.tipo_propiedad) filtros.tipo_propiedad = vistos.ultimo.tipo_propiedad;
            abrirModal({ tipo: 'popup', filtros: filtros, resumen: resumenFiltros(filtros) });
        }, 6000);
    }

    iniciarSeguimientoLocal();
})();
