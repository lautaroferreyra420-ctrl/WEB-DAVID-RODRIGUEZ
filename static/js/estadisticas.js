// Contador animado de la barra de estadísticas: cuenta desde 0 cuando entra en pantalla.
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const numeros = document.querySelectorAll('.stat-numero');
        if (!numeros.length) return;

        const formato = function (n) { return n.toLocaleString('es-AR'); };
        const DURACION_MS = 1400;

        // Sin IntersectionObserver o con "reducir movimiento": se muestra el número final sin animar
        if (!('IntersectionObserver' in window) || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            numeros.forEach(function (el) { el.textContent = formato(parseInt(el.dataset.valor, 10) || 0); });
            return;
        }

        function animar(el) {
            const destino = parseInt(el.dataset.valor, 10) || 0;
            const inicio = performance.now();
            function frame(ahora) {
                const progreso = Math.min((ahora - inicio) / DURACION_MS, 1);
                const facilitado = 1 - Math.pow(1 - progreso, 3); // ease-out cubic
                el.textContent = formato(Math.round(destino * facilitado));
                if (progreso < 1) requestAnimationFrame(frame); else el.textContent = formato(destino);
            }
            requestAnimationFrame(frame);
        }

        const observador = new IntersectionObserver(function (entradas) {
            entradas.forEach(function (entrada) {
                if (entrada.isIntersecting) { animar(entrada.target); observador.unobserve(entrada.target); }
            });
        }, { threshold: 0.4 });
        numeros.forEach(function (el) { observador.observe(el); });
    });
})();
