from flask import Flask, render_template, request, send_file
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
import plotly.graph_objs as go
import plotly.utils
import json
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import logging

app = Flask(__name__)
x = sp.Symbol('x')
transformations = standard_transformations + (implicit_multiplication_application,)

logging.basicConfig(level=logging.INFO)

def parse_input_expression(expr_str):
    try:
        expr = parse_expr(expr_str, transformations=transformations)
        return expr
    except Exception as e:
        raise ValueError("Expresión inválida. Verifica la sintaxis.") from e

def generar_pasos(expr, operacion, punto_limite=None):
    pasos = []
    if operacion == "derivar":
        derivada = sp.diff(expr, x)
        pasos.append(f"\\[f(x) = {sp.latex(expr)}\\]")
        pasos.append(f"\\[f'(x) = {sp.latex(derivada)}\\]")
        return derivada, pasos
    elif operacion == "integrar":
        integral = sp.integrate(expr, x)
        pasos.append(f"\\[\\int f(x)\\,dx = \\int {sp.latex(expr)}\\,dx = {sp.latex(integral)} + C\\]")
        return integral, pasos
    elif operacion == "limite":
        punto = sp.sympify(punto_limite or "0")
        limite = sp.limit(expr, x, punto)
        pasos.append(f"\\[\\lim_{{x \\to {sp.latex(punto)}}} {sp.latex(expr)} = {sp.latex(limite)}\\]")
        return limite, pasos
    raise ValueError("Operación no válida.")

def generar_grafico(expr_original, expr_resultado=None, operacion=None):
    rango_x = [i / 2.0 for i in range(-20, 21)]

    def evaluar(expr, val):
        try:
            resultado = expr.subs(x, val)
            return float(resultado) if resultado.is_real else None
        except:
            return None

    y_original = [evaluar(expr_original, val) for val in rango_x]
    y_resultado = [evaluar(expr_resultado, val) for val in rango_x] if expr_resultado else None

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

def generar_pdf(expr_original, expr_resultado=None, operacion=None):
    rango_x = [i / 2.0 for i in range(-20, 21)]

    def evaluar(expr, val):
        try:
            resultado = expr.subs(x, val)
            return float(resultado) if resultado.is_real else None
        except:
            return None

    y_original = [evaluar(expr_original, val) for val in rango_x]
    y_resultado = [evaluar(expr_resultado, val) for val in rango_x] if expr_resultado else None

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
    pdf_buffer = None

    if request.method == "POST":
        expresion = request.form.get("expresion", "").strip()
        operacion = request.form.get("operacion", "derivar")
        punto_limite = request.form.get("punto_limite", "0").strip()

        try:
            expr = parse_input_expression(expresion)
            resultado_sym, pasos = generar_pasos(expr, operacion, punto_limite)
            resultado = sp.latex(resultado_sym)
            grafico = generar_grafico(expr, resultado_sym if operacion in ['derivar', 'integrar'] else None, operacion)
            pdf_buffer = generar_pdf(expr, resultado_sym if operacion in ['derivar', 'integrar'] else None, operacion)
            # Guarda temporalmente en memoria
            request.environ['pdf_buffer'] = pdf_buffer
        except Exception as e:
            logging.exception("Error en procesamiento de entrada:")
            error = f"{str(e)}"

    return render_template(
        "index.html",
        resultado=resultado,
        pasos=pasos,
        grafico=grafico,
        error=error,
        expresion=expresion,
        operacion=operacion,
        punto_limite=punto_limite
    )

@app.route("/descargar")
def descargar():
    buffer = request.environ.get('pdf_buffer')
    if buffer:
        return send_file(buffer, as_attachment=True, download_name="grafico.pdf", mimetype='application/pdf')
    return "No hay gráfico disponible para descargar.", 404

if __name__ == "__main__":
    app.run(debug=True)
