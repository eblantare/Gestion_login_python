from flask_mail import Message
from run import create_app, mail

app = create_app()
with app.app_context():
    msg = Message(subject="Test Mail",
                  recipients=["ton_email@exemple.com"],
                  body="Ceci est un test depuis Flask-Mail")
    mail.send(msg)
    print("Email envoyé !")