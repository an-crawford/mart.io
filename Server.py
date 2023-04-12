from flask import Flask, request, jsonify, render_template
import extra 

app = Flask(__name__)
app.config["DEBUG"] = True
@app.route('/', methods = ['GET', 'POST'])

def adder_page():
    line = str(request.args.get('line', ''))
    id = str(request.args.get('id', ''))
    if line:
        result = extra.new_data(line, id)._repr_html_()
    else:
        result = 'None'
    return (
        """<form action="" method = "get">
                Train Line: <input name="line">
                Train ID: <input name="id">
                <input type="submit" value="Get Prediction">
            </form>"""
        + 'Map:'
        + result
    )

if __name__ == '__main__':
    app.run(port=5000)