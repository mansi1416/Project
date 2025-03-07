from flask import Flask,render_template#importing module
app=Flask(__name__)#create instance
@app.route('/')#to acceess text/funtion
def home():
    return "Hello Students!"
@app.route('/about')
def about():
    return render_template('about.html')
if __name__ == '__main__':
    app.run(debug=True)