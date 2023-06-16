from flask_mail import Mail, Message

mail = Mail()

def configure_mail(app):
    
    # Configure email settings
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = 'fmsreadonly@gmail.com'
    app.config['MAIL_PASSWORD'] = 'usfhxqhpiccbwgbl'
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_DEFAULT_SENDER'] = 'readonly@fms.com'
    
    # Initialize mail extension
    mail.init_app(app)

# Send mail function
def send_mail(subject, recipient, body, sender='readonly@fms.com'):
    # Create a message
    msg = Message(subject, recipients=[recipient], body=body, html="", sender=sender)

    # Send the message
    mail.send(msg)
