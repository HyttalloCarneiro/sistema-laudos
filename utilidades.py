from fpdf import FPDF
import os
from datetime import datetime

def gerar_certidao_ausencia(numero_processo, nome_parte, tipo, horario, data, local, nome_arquivo="certidao_ausencia.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="CERTIDÃO DE AUSÊNCIA", ln=True, align="C")
    pdf.ln(10)

    texto = (
        f"Certifico que, na data de {data.strftime('%d/%m/%Y')}, às {horario}, "
        f"no local de perícia \"{local}\", referente ao processo {numero_processo} "
        f"do tipo {tipo}, a parte autora {nome_parte} não compareceu para a realização da perícia médica designada.\n\n"
        f"Assim, lavro a presente certidão para os devidos fins."
    )

    pdf.multi_cell(0, 10, txt=texto)
    pdf.ln(20)

    pdf.cell(0, 10, txt=f"Local e data: {local}, {data.strftime('%d/%m/%Y')}", ln=True)

    os.makedirs("temp", exist_ok=True)
    caminho = os.path.join("temp", nome_arquivo)
    pdf.output(caminho)

    return caminho