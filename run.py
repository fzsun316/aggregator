from myapp import scheduler
scheduler.start()

from myapp import app, sSLContext
app.run(host='0.0.0.0', port=12344, debug=True, ssl_context = sSLContext, use_reloader=False)

