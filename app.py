import csv
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.form.to_dict()
        file_exists = os.path.isfile('submissions.csv')
        with open('submissions.csv', 'a', newline='') as f:
            # We use a preset list of fieldnames based on our form to ensure consistency
            fieldnames = ['name', 'email', 'subject', 'message']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            # Filter data to only include expected fieldnames
            filtered_data = {k: v for k, v in data.items() if k in fieldnames}
            writer.writerow(filtered_data)
        return redirect(url_for('contact'))
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
