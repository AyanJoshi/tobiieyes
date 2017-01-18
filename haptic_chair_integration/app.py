from flask import *
from jinja2 import TemplateNotFound
app = Flask(__name__)

import haptic
import random

patterns, interface, pdata = haptic.main()

@app.route('/', defaults={'page': 'index'})
@app.route('/<page>')
def show(page):
	g.json = open('patterns.json').read()
	try:
		return render_template('%s.html' % page)
	except TemplateNotFound:
		abort(404)


@app.route('/patterns')
def patt_erns():
	g.json = open('patterns.json').read()
	global patterns
	return render_template("patterns.html")


@app.route('/run/<int:num>')
def run(num):
	patterns[num]()
	return "success"


@app.route('/logger', methods=['POST'])
def logger():
	data = request.form['data']
	with open('logs.txt', 'a+') as logf:
		logf.write("\n")
		logf.write(data)
	return "success"


@app.route("/pattern/<int:num>", methods=['GET', 'POST'])
def pattern(num):
	g.json = open('patterns.json').read()
	global patterns
	if request.method == 'GET':
		if num >= patterns:
			return redirect('/end')
		patterns[num]()
		if 'XMLHttpRequest' in request.headers.get('X-Requested-With', ''):
			return jsonify(pattern=num)
		return render_template("pattern.html", num=num, pattern=patterns[num], progress=(float(num) * 100 / float(len(patterns))))
	else:
		return render_template("intermediate.html", num=(num + 1), progress=(float(num + 1) * 100 / float(len(patterns))))


if __name__ == "__main__":
	app.secret_key = "asdf"
	app.run(debug=False)
