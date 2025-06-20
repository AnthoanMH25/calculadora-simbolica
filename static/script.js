function insert(val) {
  const input = document.getElementById('expresion');
  input.value += val;
}

function borrar() {
  const input = document.getElementById('expresion');
  input.value = input.value.slice(0, -1);
}

function limpiar() {
  document.getElementById('expresion').value = '';
}

// Mostrar campo del punto del límite solo si la operación es "limite"
function mostrarCampoLimite(valor) {
  const campo = document.getElementById('campo-limite');
  if (valor === 'limite') {
    campo.style.display = 'inline-block';
  } else {
    campo.style.display = 'none';
    campo.value = ''; // Limpiar valor si no es necesario
  }
}

// Ejecutar al cargar (por si se regresa con POST)
window.onload = function () {
  const select = document.getElementById('operacion');
  mostrarCampoLimite(select.value);
};
