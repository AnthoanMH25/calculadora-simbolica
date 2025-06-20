from flask import Flask, render_template, request, send_file
import sympy as sp
import plotly.graph_objs as go
import plotly.utils
import json
from io import BytesIO
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

app = Flask(__name__)
x = sp.Symbol('x')

def generar_pasos(expr, operacion, punto_limite=None):
    pasos = []
    if operacion == "derivar":
        derivada = sp.diff(expr, x)
        pasos.append(f"\\[f(x) = {sp.latex(expr)}\\]")
        pasos.append(f"\\[f'(x) = {sp.latex(derivada)}\\]")
        return derivada, pasos
    elif operacion == "integrar":
        integral = sp.integrate(expr, x)
        pasos.append(f"\\[\\int f(x)\\,dx = \\int {sp.latex(expr)}\\,dx = {sp.latex(integral)}\\]")
        return integral, pasos
    elif operacion == "limite":
        punto = sp.sympify(punto_limite) if punto_limite else 0
        limite = sp.limit(expr, x, punto)
        pasos.append(f"\\[\\lim_{{x \\to {sp.latex(punto)}}} {sp.latex(expr)} = {sp.latex(limite)}\\]")
        return limite, pasos
    return None, ["Operación no válida."]

@app.route("/", methods=["GET", "POST"])
def index():
    resultado = ""
    pasos = []
    grafico = None
    expr_str = ""
    error = None

    if request.method == "POST":
        expr_str = request.form.get("expresion", "")
        operacion = request.form.get("operacion")
        punto_limite = request.form.get("punto_limite", "0")
        try:
            expr = sp.sympify(expr_str)
            resultado_sym, pasos = generar_pasos(expr, operacion, punto_limite)
            resultado = sp.latex(resultado_sym)

            # Elegir qué función graficar
            if operacion == "derivar" or operacion == "integrar":
                expr_para_graficar = resultado_sym
            else:
                expr_para_graficar = expr

            x_vals = list(range(-10, 11))
            y_vals_original = [float(expr.subs(x, val)) for val in x_vals]
            y_vals_operacion = [float(expr_para_graficar.subs(x, val)) for val in x_vals]

            plot = go.Figure()
            plot.add_trace(go.Scatter(x=x_vals, y=y_vals_original, mode='lines+markers', name='f(x)', line=dict(color='blue')))
            if operacion in ["derivar", "integrar"]:
                plot.add_trace(go.Scatter(x=x_vals, y=y_vals_operacion, mode='lines+markers', name='Resultado', line=dict(color='red')))
            plot.update_layout(title="Gráfica de la función", xaxis_title="x", yaxis_title="y")
            grafico = json.dumps(plot, cls=plotly.utils.PlotlyJSONEncoder)

            # PDF
            buffer = BytesIO()
            with PdfPages(buffer) as pdf:
                fig, ax = plt.subplots()
                ax.plot(x_vals, y_vals_original, marker='o', label='f(x)')
                if operacion in ["derivar", "integrar"]:
                    ax.plot(x_vals, y_vals_operacion, marker='x', label='Resultado')
                ax.set_title("Gráfica de la función")
                ax.set_xlabel("x")
                ax.set_ylabel("y")
                ax.legend()
                pdf.savefig(fig)
                plt.close(fig)
            buffer.seek(0)
            with open("static/output.pdf", "wb") as f:
                f.write(buffer.read())

        except Exception as e:
            error = str(e)

    return render_template("index.html", resultado=resultado, pasos=pasos, grafico=grafico, expresion=expr_str, error=error)

@app.route("/descargar")
def descargar():
    return send_file("static/output.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)