from flask import Flask, request, send_file, jsonify, render_template
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Annotation data storage (example: using an in-memory dictionary, use a database in production)
annotations = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return jsonify({"filename": file.filename}), 201
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/pdf/<filename>')
def get_pdf(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), mimetype='application/pdf')

@app.route('/annotations', methods=['GET', 'POST'])
def manage_annotations():
    if request.method == 'POST':
        new_annotation = request.json
        new_annotation['id'] = len(annotations) + 1
        annotations.append(new_annotation)
        return jsonify(new_annotation), 201
    else:
        return jsonify(annotations)

@app.route('/annotations/<int:annot_id>', methods=['PUT', 'DELETE'])
def update_annotation(annot_id):
    annotation = next((annot for annot in annotations if annot['id'] == annot_id), None)
    if annotation is None:
        return jsonify({"error": "Annotation not found"}), 404

    if request.method == 'PUT':
        data = request.json
        annotation.update(data)
        return jsonify(annotation)
    elif request.method == 'DELETE':
        annotations.remove(annotation)
        return '', 204

if __name__ == "__main__":
    app.run(debug=True)
