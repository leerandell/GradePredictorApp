from website import create_app

app = create_app()

if __name__ == '__main__':
  app.run(debug=False) #This line of code automatically rerun the web server. Turn it off when running it on production