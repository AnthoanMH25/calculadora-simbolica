from flask import Flask, render_template, request, send_file
import sympy as sp
import plotly.graph_objs as go
import plotly.utils
import json
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import re

app = Flask(__name__)
x = sp.Symbol('x')


def corregir_multiplicacion_implicita(expr_str: str) -> str:
    """
    Corrige multiplicaciones implícitas para que sympy las entienda correctamente.
    """
    # 1. Número seguido de variable: 5x -> 5*x
    expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)
    
    # 2. Variable seguida de paréntesis: x(x+1) -> x*(x+1)
    expr_str = re.sub(r'([a-zA-Z])(\()', r'\1*\2', expr_str)
    
    # 3. Paréntesis seguidos de variable: (x+1)x -> (x+1)*x
    expr_str = re.sub(r'(\))([a-zA-Z])', r'\1*\2', expr_str)
    
    # 4. Número seguido de paréntesis: 3(x+1) -> 3*(x+1)
    expr_str = re.sub(r'(\d)(\()', r'\1*\2', expr_str)
    
    # 5. Paréntesis seguidos de paréntesis: (x+1)(x-1) -> (x+1)*(x-1)
    expr_str = re.sub(r'(\))(\()', r'\1*\2', expr_str)
    
    return expr_str


def generar_pasos(expr, operacion, punto_limite=None):
    pasos = []

    def explicar_derivacion(expr):
        partes = expr.as_ordered_terms() if expr.is_Add else [expr]
        derivada_total = 0
        for i, termino in enumerate(partes, 1):
            derivado = sp.diff(termino, x)
            regla = ""
            if termino.is_Pow:
                regla = "Regla de la potencia"
            elif termino.is_Mul:
                regla = "Regla del producto"
            elif termino.is_Function:
                if termino.has(sp.sin):
                    regla = "Regla de la derivada del seno"
                elif termino.has(sp.cos):
                    regla = "Regla de la derivada del coseno"
                elif termino.has(sp.exp):
                    regla = "Regla de la exponencial"
                elif termino.has(sp.log):
                    regla = "Regla del logaritmo natural"
                else:
                    regla = "Regla general de funciones"
            else:
                regla = "Regla de la derivada constante o lineal"

            pasos.append(f"Paso {i}: Derivamos \\({sp.latex(termino)}\\) usando **{regla}**:")
            pasos.append(f"\\[\\frac{{d}}{{dx}} {sp.latex(termino)} = {sp.latex(derivado)}\\]")
            derivada_total += derivado

        pasos.append("Sumamos todas las derivadas parciales:")
        pasos.append(f"\\[f'(x) = {sp.latex(derivada_total)}\\]")
        return derivada_total

    if operacion == "derivar":
        pasos.append("Paso 0: Identificamos la función a derivar:")
        pasos.append(f"\\[f(x) = {sp.latex(expr)}\\]")
        resultado = explicar_derivacion(expr)
        pasos.append("Paso final: Esta es la derivada simplificada de la función original.")
        return resultado, pasos

    elif operacion == "integrar":
        integral = sp.integrate(expr, x)
        pasos.append("Paso 1: Identificamos la función a integrar:")
        pasos.append(f"\\[f(x) = {sp.latex(expr)}\\]")

        if expr.has(sp.sin):
            regla = "Regla de la integral del seno: \\(\\int \\sin(x)dx = -\\cos(x) + C\\)"
        elif expr.has(sp.cos):
            regla = "Regla de la integral del coseno: \\(\\int \\cos(x)dx = \\sin(x) + C\\)"
        elif expr.has(sp.exp):
            regla = "Regla de la exponencial: \\(\\int e^x dx = e^x + C\\)"
        elif expr.has(sp.log):
            regla = "Integral del logaritmo: \\(\\int \\log(x) dx = x\\log(x) - x + C\\)"
        else:
            regla = "Se aplica la regla de potencias o lineales según corresponda."

        pasos.append(f"Paso 2: Usamos la regla correspondiente: {regla}")
        pasos.append(f"Paso 3: Resultado de la integral:")
        pasos.append(f"\\[\\int f(x)dx = {sp.latex(integral)} + C\\]")
        return integral, pasos

    elif operacion == "limite":
        try:
            punto = sp.sympify(punto_limite) if punto_limite else 0
        except Exception:
            punto = 0
        limite = sp.limit(expr, x, punto)
        pasos.append(f"Paso 1: Queremos calcular el siguiente límite:")
        pasos.append(f"\\[\\lim_{{x \\to {sp.latex(punto)}}} {sp.latex(expr)}\\]")

        if expr.has(sp.sin) or expr.has(sp.cos):
            pasos.append("Paso 2: Se detecta función trigonométrica. Verificamos continuidad.")
        elif expr.has(sp.exp):
            pasos.append("Paso 2: Se detecta función exponencial, la cual es continua.")
        elif expr.has(sp.log):
            pasos.append("Paso 2: Se detecta logaritmo. Aseguramos que el argumento sea positivo.")

        pasos.append("Paso 3: Evaluamos directamente (si es posible):")
        pasos.append(f"\\[\\lim_{{x \\to {sp.latex(punto)}}} = {sp.latex(limite)}\\]")
        pasos.append("Paso final: Este es el valor límite de la función.")
        return limite, pasos

    return None, ["Operación no válida."]


def generar_grafico(expr_original, expr_resultado=None, operacion=None):
    rango_x = [i / 2.0 for i in range(-20, 21)]

    def eval_expr(expr, val):
        try:
            resultado = expr.subs(x, val)
            if resultado.is_real:
                return float(resultado)
        except Exception:
            return None

    y_original = [eval_expr(expr_original, val) for val in rango_x]
    y_resultado = [eval_expr(expr_resultado, val) for val in rango_x] if expr_resultado else None

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rango_x, y=y_original, mode='lines+markers', name='f(x)', line=dict(color='blue')))
    if operacion in ['derivar', 'integrar'] and y_resultado:
        fig.add_trace(go.Scatter(x=rango_x, y=y_resultado, mode='lines+markers', name='Resultado', line=dict(color='red')))
    fig.update_layout(
        title="Gráfica de la función",
        xaxis_title="x",
        yaxis_title="y",
        template="plotly_dark"
    )
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def guardar_pdf(expr_original, expr_resultado=None, operacion=None):
    rango_x = [i / 2.0 for i in range(-20, 21)]

    def eval_expr(expr, val):
        try:
            resultado = expr.subs(x, val)
            if resultado.is_real:
                return float(resultado)
        except Exception:
            return None

    y_original = [eval_expr(expr_original, val) for val in rango_x]
    y_resultado = [eval_expr(expr_resultado, val) for val in rango_x] if expr_resultado else None

    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(rango_x, y_original, marker='o', label='f(x)', color='deepskyblue')
        if operacion in ['derivar', 'integrar'] and y_resultado:
            ax.plot(rango_x, y_resultado, marker='x', label='Resultado', color='orangered')
        ax.set_title('Gráfica de la función')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend()
        pdf.savefig(fig)
        plt.close(fig)
    buffer.seek(0)
    return buffer


@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    pasos = []
    grafico = None
    error = None
    expresion = ""
    operacion = "derivar"
    punto_limite = "0"

    if request.method == "POST":
        expresion = request.form.get("expresion", "").strip()
        operacion = request.form.get("operacion", "derivar")
        punto_limite = request.form.get("punto_limite", "0").strip()

        try:
            expresion_corregida = corregir_multiplicacion_implicita(expresion)
            expr = sp.sympify(expresion_corregida)
            resultado_sym, pasos = generar_pasos(expr, operacion, punto_limite)
            resultado = sp.latex(resultado_sym)

            grafico = generar_grafico(expr, resultado_sym if operacion in ['derivar', 'integrar'] else None, operacion)

            pdf_buffer = guardar_pdf(expr, resultado_sym if operacion in ['derivar', 'integrar'] else None, operacion)
            with open("static/output.pdf", "wb") as f:
                f.write(pdf_buffer.read())

        except Exception as e:
            error = f"Error al procesar la expresión: {str(e)}"

    return render_template(
        "index.html",
        resultado=resultado,
        pasos=pasos,
        grafico=grafico,
        error=error,
        expresion=expresion,
        operacion=operacion,
        punto_limite=punto_limite,
    )


@app.route("/descargar")
def descargar():
    return send_file("static/output.pdf", as_attachment=True, download_name="grafico.pdf", mimetype='application/pdf')


if __name__ == "__main__":
    app.run(debug=True)
