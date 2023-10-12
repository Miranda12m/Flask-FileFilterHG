import os
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
bootstrap = Bootstrap(app)

#-----------------------------------------------------------------
#Main templates 
#---------------------
@app.route('/itiva')
def upload_form():
    return render_template('upload.html')

@app.route('/itiva/terms_conditions')
def terms_conditions():
    return render_template('terms.html')

@app.route('/itiva/free_kitten')
def free_kitten():
    return render_template('kitten.html')


#-----------------------------------------------------------------
#404 Errors 
#---------------------
@app.errorhandler(404)
def page_not_found(e):
    if request.path.startswith('/itiva/'):
        return render_template('404.html'), 404
    else:
        return "Page not found", 404


#-----------------------------------------------------------------
#Test templates 
#---------------------
@app.route('/itiva/login')
def login():
    return render_template('login.html')


#-----------------------------------------------------------------

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['pdf', 'xml'])

def allowed_file(filename):
    valid = (
        '.' in str(filename)
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        and len(str(filename)) <= 34
    )
    if not valid:
        flash(f'Archivo(s) inválido, Revisar Requerimientos Generales')

    return valid

def check_string_length(files):
    max_string_length = 34
    for base_filename, file in files.items():
        
        if len(str(base_filename)) < 1 or len(str(base_filename)) > max_string_length:
            return f"Archivo(s) inválido, Revisar Requerimientos Generales"
        
    return None  

def check_total_file_count(pdf_files, xml_files):
    max_total_files = 50
    total_files = len(pdf_files) + len(xml_files)
    if total_files > max_total_files:
        return f"Archivo(s) inválido, Revisar Requerimientos Generales"

    return None  # Total files are within the allowed limit

@app.route('/itiva', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        pdf_files = {}
        xml_files = {}
        invalid_filenames = []

        for file in request.files.getlist('files[]'):
            if file:
                filename = secure_filename(file.filename)

                if len(filename) > 34:
                    invalid_filenames.append(filename)
                    continue

                base_filename, extension = os.path.splitext(filename)

                if extension == '.pdf':
                    pdf_files[base_filename] = file
                elif extension == '.xml':
                    xml_files[base_filename] = file

        if invalid_filenames:
            for invalid_filename in invalid_filenames:
                flash(f"Archivo(s) inválido, Revisar Requerimientos Generales")
            return redirect(request.url)

        # Check if there's a matching XML file for each PDF file
        if len(pdf_files) != len(xml_files):
            flash(f"Archivo(s) inválido, Revisar Requerimientos Generales")
            return redirect(request.url)

        # Check for matching PDF and XML files
        for pdf_base in pdf_files:
            if pdf_base not in xml_files:
                flash(f"Archivo(s) inválido, Revisar Requerimientos Generales")
                return redirect(request.url)

        for xml_base in xml_files:
            if xml_base not in pdf_files:
                flash(f"Archivo(s) inválido, Revisar Requerimientos Generales")
                return redirect(request.url)

        # ChatGPT code that currently don't undesteand how it works but... it works
        string_length_error = check_string_length(xml_files)
        if string_length_error:
            flash(string_length_error)
            return redirect(request.url)

        total_file_count_error = check_total_file_count(pdf_files, xml_files)
        if total_file_count_error:
            flash(total_file_count_error)
            return redirect(request.url)

        # Email confirm
        send_files_by_email(pdf_files, xml_files)

        flash('Archivos procesados correctamente')
        return redirect('/itiva')



def send_files_by_email(pdf_files, xml_files):
    # Email config
    EMAIL_ADDRESS = "hapaglloydmexicobot@gmail.com"  
    EMAIL_PASSWORD = "apdzeotkoypukelj" 
    EMAIL_TO = "MXITIVA@hlag.com"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_TO
    msg['Subject'] = 'Archivos Adjuntos'

    # Cuerpo del correo
    body = 'Archivos adjuntos desde la aplicación Flask:'
    msg.attach(MIMEText(body, 'plain'))

    # Adjunta los archivos a enviar
    for pdf_base, pdf_file in pdf_files.items():
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_file.read())  # Lee el contenido del archivo
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {pdf_base}.pdf")  # Cambia el nombre del archivo si es necesario
        msg.attach(part)

    for xml_base, xml_file in xml_files.items():
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(xml_file.read())  # Lee el contenido del archivo
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {xml_base}.xml")  # Cambia el nombre del archivo si es necesario
        msg.attach(part)

    # ---
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, EMAIL_TO, text)
        server.quit()
    except Exception as e:
        flash(f'Error sending email: {str(e)}')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)