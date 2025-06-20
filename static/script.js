document.addEventListener("DOMContentLoaded", () => {
  const expresionInput = document.getElementById("expresion");
  const operacionSelect = document.getElementById("operacion");
  const puntoLimiteInput = document.getElementById("punto_limite");
  const spinner = document.getElementById("spinner");
  const form = document.querySelector("form");

  /**
   * Muestra u oculta el campo de punto según la operación.
   */
  function togglePuntoLimite() {
    const mostrar = operacionSelect.value === "limite";
    puntoLimiteInput.closest(".mb-3").style.display = mostrar ? "block" : "none";
  }

  /**
   * Inserta símbolo o función matemática en el input actual.
   * @param {string} simbolo - símbolo como "x", "+", "sqrt()"
   */
  function insertarSimbolo(simbolo) {
    const cursorPos = expresionInput.selectionStart;
    const isFuncion = simbolo.endsWith("()");
    const textoInsertar = isFuncion
      ? simbolo.slice(0, -2) + "()" // ej: sqrt()
      : simbolo;

    const antes = expresionInput.value.slice(0, cursorPos);
    const despues = expresionInput.value.slice(expresionInput.selectionEnd);
    expresionInput.value = antes + textoInsertar + despues;

    expresionInput.focus();
    const nuevaPos = isFuncion ? cursorPos + textoInsertar.length - 1 : cursorPos + textoInsertar.length;
    expresionInput.setSelectionRange(nuevaPos, nuevaPos);
  }

  /**
   * Activa los eventos de los botones de símbolos.
   */
  function inicializarBotonesSimbolo() {
    document.querySelectorAll(".btn-simbolo").forEach((btn) => {
      btn.addEventListener("click", () => {
        const simbolo = btn.getAttribute("data-simbolo");
        insertarSimbolo(simbolo);
      });
    });
  }

  /**
   * Muestra el spinner al enviar el formulario.
   */
  function prepararFormulario() {
    form.addEventListener("submit", () => {
      spinner?.classList.remove("d-none");
    });
  }

  // === INICIALIZACIÓN ===
  togglePuntoLimite();
  inicializarBotonesSimbolo();
  prepararFormulario();
  operacionSelect.addEventListener("change", togglePuntoLimite);
});
