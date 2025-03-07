from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from utils import load_data, get_summary_statistics, get_column_types
import plotly
import plotly.express as px
import traceback

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.debug = True

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering index: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        print(f"Attempting to load file: {file.filename}")  # Debug log
        df = load_data(file)

        if df is None:
            return jsonify({'error': 'Invalid file format or error loading file'}), 400

        # Get column information
        numerical_cols, categorical_cols = get_column_types(df)

        # Get summary statistics
        summary_stats = get_summary_statistics(df).to_dict()

        # Convert DataFrame info to JSON
        columns = df.columns.tolist()
        preview = df.head().to_dict('records')

        return jsonify({
            'columns': columns,
            'numerical_columns': numerical_cols,
            'categorical_columns': categorical_cols,
            'preview': preview,
            'summary': summary_stats
        })

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 400

@app.route('/visualize', methods=['POST'])
def create_visualization():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        print(f"Received visualization request:")
        print(f"Chart type: {data.get('chartType')}")
        print(f"X Column: {data.get('xColumn')}")
        print(f"Y Column: {data.get('yColumn')}")

        # Convert data to DataFrame
        try:
            file_content = pd.DataFrame(data['data'])
            print(f"Data shape: {file_content.shape}")
            print(f"Columns: {file_content.columns.tolist()}")
        except Exception as e:
            print(f"Error converting data to DataFrame: {str(e)}")
            return jsonify({'error': 'Invalid data format'}), 400

        chart_type = data['chartType']
        x_col = data['xColumn']
        y_col = data.get('yColumn')
        title = data.get('title', 'Visualization')

        # Validate columns
        if x_col not in file_content.columns:
            return jsonify({'error': f'Column {x_col} not found in data'}), 400
        if chart_type != 'histogram' and y_col not in file_content.columns:
            return jsonify({'error': f'Column {y_col} not found in data'}), 400

        try:
            if chart_type == 'line':
                fig = px.line(file_content, x=x_col, y=y_col, title=title)
            elif chart_type == 'bar':
                fig = px.bar(file_content, x=x_col, y=y_col, title=title)
            elif chart_type == 'scatter':
                fig = px.scatter(file_content, x=x_col, y=y_col, title=title)
            elif chart_type == 'histogram':
                fig = px.histogram(file_content, x=x_col, title=title)
            else:
                return jsonify({'error': f'Invalid chart type: {chart_type}'}), 400

            # Add layout configurations
            fig.update_layout(
                autosize=True,
                height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )

            # Convert to JSON
            try:
                graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
                print("Successfully created visualization")
                return jsonify({'chart': graphJSON})
            except Exception as e:
                print(f"Error converting plot to JSON: {str(e)}")
                return jsonify({'error': 'Error serializing plot'}), 500

        except Exception as e:
            print(f"Error creating plot: {str(e)}")
            return jsonify({'error': f'Error creating {chart_type} plot'}), 400

    except Exception as e:
        print(f"Error in visualization endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    print("Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, threaded=True)