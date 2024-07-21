@app.route('/count')
def display_count():
    counts = Count.query.all()
    return render_template('count.html', counts=counts)